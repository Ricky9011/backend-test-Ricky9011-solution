from celery import shared_task
from django.conf import settings
from django.db import transaction
from sentry_sdk import start_transaction

from core.event_log_client import EventLogClient
from core.models import OutboxEvent


@shared_task(autoretry_for=(Exception,), retry_backoff=True)
def process_outbox() -> None:
    with start_transaction(op="celery_task", name="process_outbox"):

        batch_size = settings.CH_OUTBOX_BATCH_SIZE

        with transaction.atomic():
            events = OutboxEvent.objects.select_for_update(skip_locked=True).filter(processed=False)[:batch_size]
            if not events:
                return

            with EventLogClient.init() as client:
                client.insert(events)

            events.update(processed=True)
