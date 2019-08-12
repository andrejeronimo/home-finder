import requests
import re
import json

from lxml import html
from django_telegrambot.apps import DjangoTelegramBot
from celery.task import task

from crawlers.models import ArticleSchema
from crawlers.models import Article
from crawlers.models import Task


# Request headers
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9'
}


class CrawlerEngine:

    @classmethod
    def crawl(cls, task, max_pages=2):

        new_articles = list()

        crawler = task.crawler
        page_url = task.search_url
        page_number = 1

        stop = False

        # Check if this is the first run
        if not task.timestamp:
            first_run = True
            max_pages = 1
        else:
            first_run = False

        # Update crawl task timestamp
        task.update_timestamp()

        while page_url and (not stop) and (not max_pages or page_number <= max_pages):

            # Read page html
            page = requests.get(page_url, headers=REQUEST_HEADERS)

            # Parse page
            tree = html.fromstring(page.content)

            # Find articles
            articles = tree.xpath(crawler.articles)

            # Iterate over the articles
            for a in articles:

                # Parse article
                article = cls._parse_article(a, crawler)

                if not article:
                    continue

                # Create the article snapshot in the database
                _, created = Article.objects.get_or_create(task=task,
                                                           article_id=article.id)

                if created:

                    if not first_run:

                        # Send article to user
                        new_articles.append(article)

                else:  # If this article has already been crawled we stop (no more new articles to crawl)
                    stop = True

            # Read next page
            try:
                page_url = tree.xpath(crawler.next_page_url)[0]
            except IndexError:
                page_url = None

            page_number += 1

        return new_articles

    @classmethod
    def _parse_article(cls, article_html, crawler):

        article = ArticleSchema()

        # Id
        try:
            article.id = cls._converter(article_html.xpath(crawler.article_id))
        except IndexError:
            return None

        # Url
        try:
            article.url = cls._converter(article_html.xpath(crawler.article_url))
        except IndexError:
            return None

        # Title
        if crawler.article_title:
            try:
                article.title = cls._converter(article_html.xpath(crawler.article_title))
                article.title = cls._clean_text(article.title)
            except IndexError:
                pass

        # Image
        if crawler.article_image:
            try:
                article.image = cls._converter(article_html.xpath(crawler.article_image))
            except IndexError:
                pass

        # Description
        if crawler.article_description:
            try:
                article.description = cls._converter(article_html.xpath(crawler.article_description))
                article.description = cls._clean_text(article.description)
            except IndexError:
                pass

        # Price
        if crawler.article_price:
            try:
                article.price = cls._converter(article_html.xpath(crawler.article_price))
                article.price = cls._clean_text(article.price)
            except IndexError:
                pass

        return article

    @classmethod
    def _clean_text(cls, text):
        cleaned_text = re.sub(r"[\n\t\s]+", " ", text.strip())
        return cleaned_text

    @classmethod
    def _converter(cls, s):
        return s[0] if isinstance(s, list) else s


@task
def run_task(task_id):

    # Get task
    try:
        t = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        return []

    # Get new articles
    articles = CrawlerEngine.crawl(t)

    # Send articles to user
    bot = DjangoTelegramBot.bots[0]

    for article in articles:
        bot.sendMessage(t.user.telegram_id, text=article.to_message())
