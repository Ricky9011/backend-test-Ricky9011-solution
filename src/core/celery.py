import os

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

app.config_from_object(settings, namespace="CELERY")

app.autodiscover_tasks()

from celery.schedules import crontab

# schedule period tasks
app.conf.beat_schedule = {
    "process_outbox": {
        "task": "log_manager.tasks.process_outbox",
        "schedule": crontab(minute="*/1"),  # run task every minute
    },
}
