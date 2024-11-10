# core/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.update(
    CELERY_BROKER_URL='redis://localhost:6379/0',  # Redis connection string
    CELERY_RESULT_BACKEND='redis://localhost:6379/0',
)


# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
