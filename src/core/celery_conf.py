import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")

celery_app = Celery("core", broker=settings.REDIS_URL)
celery_app.config_from_object("django.conf:settings", namespace="CELERY")

celery_app.autodiscover_tasks()

minute, hour, day_of_month, month_of_year, day_of_week = settings.OUTBOX_TASK_CRON.split()

celery_app.conf.beat_schedule = {
    "process-outbox-every-minute": {
        "task": "logs.tasks.process_outbox_task",
        "schedule": crontab(
            minute=minute,
            hour=hour,
            day_of_month=day_of_month,
            month_of_year=month_of_year,
            day_of_week=day_of_week,
        ),
        "args": (settings.LOG_BATCH_SIZE,),
    },
}