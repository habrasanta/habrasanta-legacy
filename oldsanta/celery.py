import os

from django.conf import settings

from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oldsanta.settings')


app = Celery('oldsanta')


app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
