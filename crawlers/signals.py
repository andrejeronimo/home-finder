from django.db.models.signals import post_save
from django.db.models.signals import post_delete
from django.dispatch import receiver

from crawlers.models import Task
from crawlers.scheduler import schedule_task
from crawlers.scheduler import unschedule_task



