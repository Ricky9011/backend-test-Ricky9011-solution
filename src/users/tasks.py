from celery import shared_task
from django.conf import settings
from django.db import transaction
from clickhouse_connect.driver.exceptions import DatabaseError

from core.event_log_client import EventLogClient
from users.models import EventOutbox


@shared_task
def process_outbox_events(batch_size=settings.CLICKHOUSE_BATCH_SIZE):
    """
    Task for adding events from EventOutbox db table to ClickHouse table, using batches.
    If the number of events in the EventOutbox table is less than the batch size, no action is taken.
    """
    events = EventOutbox.objects.order_by("event_date_time")
    while True:
        cur_batch_events = list(events[:batch_size])
        if len(cur_batch_events) < settings.CLICKHOUSE_BATCH_SIZE:
            break

        batch_data = [
            (
                event.event_type,
                event.event_date_time,
                event.environment,
                event.event_context,
            )
            for event in cur_batch_events
        ]

        # Insert the data into ClickHouse
        try:
            with transaction.atomic():
                with EventLogClient.init() as client:
                    client.insert(data=batch_data)

                event_ids = [event.id for event in cur_batch_events]
                EventOutbox.objects.filter(id__in=event_ids).delete()

            events = EventOutbox.objects.order_by("event_date_time").exclude(id__in=event_ids)
        except DatabaseError:
            pass

