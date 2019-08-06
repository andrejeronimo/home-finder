from django.db import models


class User(models.Model):

    # Telegram id
    telegram_id = models.IntegerField(null=False, blank=False, unique=True)

    # Name
    name = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return str(self.telegram_id)
