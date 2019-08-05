from django.conf.urls import include
from django.conf.urls import url
from django.contrib import admin


urlpatterns = [
    url('admin/', admin.site.urls),
    url(r'^', include('django_telegrambot.urls'))
]
