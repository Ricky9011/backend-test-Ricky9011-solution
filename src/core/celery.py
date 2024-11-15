from celery import Celery
from django.conf import settings

app = Celery("core")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Define periodic tasks for log processing
app.conf.beat_schedule = {
    "process-outbox-every-minute": {
        "task": "logs.tasks.process_outbox_task",
        "schedule": 60.0,  # Run every minute
        "args": (settings.LOG_BATCH_SIZE,),  # Pass batch size dynamically
    },
}
