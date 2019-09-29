from django.core.management.base import BaseCommand, CommandError
from crawlers.models import Crawler, Task
from crawlers.crawler_engine import CrawlerEngine

class Command(BaseCommand):
    help = "Test a crawler using a custom search url in order to check if the crawler is valid"

    def add_arguments(self, parser):
        parser.add_argument('-u', '--url', dest='url', type=str)
        parser.add_argument('-c', '--crawler_id', dest='crawler_id', type=int)

    def handle(self, *args, **options):
        crawler_id = options['crawler_id']
        url = options['url']

        if crawler_id is None:
            print("No Crawler ID submitted")
            return
        else:
            try:
                crawler = Crawler.objects.get(pk=crawler_id)
            except Crawler.DoesNotExist:
                print("Crawler with ID %d does not exist" % crawler_id)
                return

        if url is None:
            print("No Url was passed")
            return


        print("Testing craweler %s" % crawler.name)

        test_task = Task(search_url=url, crawler=crawler)
        CrawlerEngine.test_crawl(test_task)