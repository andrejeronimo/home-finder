from django.contrib import admin

from crawlers.models import Crawler
from crawlers.models import Task
from crawlers.models import Article


class CrawlerAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'url']


class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'crawler']


admin.site.register(Crawler, CrawlerAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Article)