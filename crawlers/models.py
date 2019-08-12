from datetime import datetime

from django.db import models
from django.db.models.signals import post_save
from django.db.models.signals import post_delete
from django.dispatch import receiver

from users.models import User


class Crawler(models.Model):

    # Name
    name = models.CharField(max_length=50, blank=False, null=False, unique=True)

    # Url
    url = models.CharField(max_length=200, blank=False, null=False)

    # XPATH fields

    # Articles
    articles = models.CharField(max_length=200, blank=False, null=False)

    # Article id
    article_id = models.CharField(max_length=200, blank=False, null=False)

    # Article url
    article_url = models.CharField(max_length=200, blank=False, null=False)

    # Article title
    article_title = models.CharField(max_length=200, blank=True, null=True)

    # Article image
    article_image = models.CharField(max_length=200, blank=True, null=True)

    # Article description
    article_description = models.CharField(max_length=200, blank=True, null=True)

    # Article price
    article_price = models.CharField(max_length=200, blank=True, null=True)

    # Next page url
    next_page_url = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name


class Task(models.Model):

    # User
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Crawler
    crawler = models.ForeignKey(Crawler, on_delete=models.CASCADE)

    # Search url
    search_url = models.CharField(max_length=200, blank=False, null=False)

    # Time interval in minutes (default is 30 minutes)
    time_interval = models.PositiveIntegerField(blank=False, null=False, default=30)

    # Timestamp
    timestamp = models.DateTimeField(null=True, blank=True, default=None)

    # Active flag
    active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.pk)

    def update_timestamp(self):
        self.timestamp = datetime.now()
        self.save(update_fields=['timestamp'])


@receiver(post_save, sender=Task)
def signal_create_task(sender, instance, created, **kwargs):
    if created:
        from crawlers.scheduler import schedule_task
        schedule_task(instance)


@receiver(post_delete, sender=Task)
def signal_delete_task(sender, instance, **kwargs):
    from crawlers.scheduler import unschedule_task
    unschedule_task(instance)


class Article(models.Model):

    # Task
    task = models.ForeignKey(Task, on_delete=models.CASCADE)

    # Article id
    article_id = models.CharField(max_length=200, blank=False, null=False)

    class Meta:
        unique_together = ('task', 'article_id')


class ArticleSchema(object):

    def __init__(self, id=None, url=None, title=None, image=None, description=None, price=None):
        self.id = id
        self.url = url
        self.title = title
        self.image = image
        self.description = description
        self.price = price

    def to_message(self):
        message = ""

        # Title
        if self.title:
            message += "%s\n" % self.title

        # Price
        if self.price:
            message += "%s\n" % self.price

        # Url
        if self.url:
            message += "%s\n" % self.url

        return message
