import json

import structlog
from celery import shared_task
from django.conf import settings
from django.db.models import F
from django.utils import timezone
from sentry_sdk import start_transaction

from core.event_log_client import EventLogClient
from core.models import OutboxEvent

logger = structlog.get_logger(__name__)

@shared_task
def process_outbox_events() -> None:
   """
   Celery task that processes pending events from the outbox.
   Groups them into batches and sends to ClickHouse.
   Flow:
   1. Get batch of pending events from outbox
   2. Convert them to ClickHouse format
   3. Send batch to ClickHouse
   4. Mark processed events as completed
   5. Handle any errors and mark failed events
   """
   # Start Sentry transaction for monitoring
   with start_transaction(op="process_events", name="process_outbox_events") as transaction:
       # Get batch of pending events
       batch_size = settings.CLICKHOUSE_BATCH_SIZE
       events = OutboxEvent.objects.filter(
           status=OutboxEvent.STATUS_PENDING,
       ).order_by('created_at')[:batch_size]

       events_list = list(events)
       if not events_list:
           return

       # Add batch size info to Sentry transaction
       transaction.set_data("batch_size", len(events_list))

       try:
           with EventLogClient.init() as client:
               # Convert events to ClickHouse format - sort keys for consistent JSON
               clickhouse_events = [
                   (
                       event.event_type,
                       event.created_at,
                       settings.ENVIRONMENT,
                       json.dumps(
                           dict(sorted(event.event_data.items())),
                           separators=(',', ':'),
                       ),
                       1,  # metadata_version
                   )
                   for event in events_list
               ]

               # Send batch to ClickHouse
               client.insert(
                   table='event_log',
                   data=clickhouse_events,
                   column_names=[
                       'event_type',
                       'event_date_time',
                       'environment',
                       'event_context',
                       'metadata_version',
                   ],
               )

               # Mark events as successfully processed
               now = timezone.now()
               processed_count = OutboxEvent.objects.filter(
                   id__in=[e.id for e in events_list],
               ).update(
                   status=OutboxEvent.STATUS_PROCESSED,
                   processed_at=now,
               )

               logger.info(
                   "processed_outbox_events_batch",
                   count=processed_count,
               )

               # Add success metrics to Sentry transaction
               transaction.set_data("processed_count", processed_count)
               transaction.set_status("ok")

       except Exception as e:
           # Log error details
           logger.error(
               "failed_to_process_outbox_events",
               error=str(e),
               exc_info=True,  # Include stack trace
           )

           # Mark events as failed and increment retry counter
           failed_count = OutboxEvent.objects.filter(
               id__in=[e.id for e in events_list],
           ).update(
               status=OutboxEvent.STATUS_FAILED,
               error_message=str(e),
               retry_count=F('retry_count') + 1,
           )

           # Add error info to Sentry transaction
           transaction.set_data("failed_count", failed_count)
           transaction.set_status("internal_error")
           transaction.set_data("error", str(e))
