import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from celery import Celery
from django.conf import settings


app = Celery('tasks', broker=settings.CELERY_BROKER, backend=settings.CELERY_BROKER)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

