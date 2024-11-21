import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.core.settings")

app = Celery("challenge")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.broker_connection_retry_on_startup = True

app.conf.beat_schedule = {
    "export_outbox_logs": {
        "task": "src.logs.tasks.export_outbox_logs",
        "schedule": crontab(minute="*"),  # every minute
    },
    "cleanup_outbox_logs": {
        "task": "src.logs.tasks.cleanup_outbox_logs",
        "schedule": crontab(minute="0", hour="0"),  # every day
    },
}
