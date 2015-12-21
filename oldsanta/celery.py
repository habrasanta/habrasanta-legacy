import os

from django.conf import settings

from celery import Celery


app = Celery('oldsanta')


app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
