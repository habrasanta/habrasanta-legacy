import os

from django.conf import settings

from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsanta.settings')


app = Celery('newsanta')


app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
