from django.contrib import admin

from users.models import User


class UserAdmin(admin.ModelAdmin):
    fields = ['id', 'telegram_id', 'name']


admin.site.register(User, UserAdmin)
