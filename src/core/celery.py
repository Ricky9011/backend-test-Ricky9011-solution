import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery("core")
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'process_outbox_events': {
        'task': 'users.tasks.process_outbox_events',
        'schedule': crontab(minute=f"*/{settings.CLICKHOUSE_UPDATE_INTERVAL}"),  # Every 10 minutes
    },
}
