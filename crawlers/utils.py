from urllib.parse import urlparse

from crawlers.models import Crawler
from crawlers.models import Task
from crawlers.scheduler import schedule_task


def validate_crawler(name):

    try:
        Crawler.objects.get(name__iexact=name)
    except Crawler.DoesNotExist:
        return False

    return True


def validate_task_link(crawler, link):

    # Check if link belongs to the same domain of the crawler url
    crawler_url_domain = extract_domain(crawler.url)
    link_domain = extract_domain(link)

    if crawler_url_domain != link_domain:
        return False

    return True


def extract_domain(link):
    domain = urlparse(link).netloc.lower()

    if domain.startswith("www."):
        domain = domain[4:]

    return domain


def create_task(user, crawler, link):

    task = Task.objects.create(user=user,
                               crawler=crawler,
                               search_url=link,
                               time_interval=15)

    return task


def get_tasks(user):
    tasks = Task.objects.filter(user=user, active=True).order_by('pk')
    return list(tasks)


def delete_task(task):
    task.delete()
