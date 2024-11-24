import structlog
from celery import shared_task
from django.utils.timezone import now

from core.event_log_client import EventLogClient

from .models import EventOutbox

# Get the logger for this module
logger = structlog.get_logger()

@shared_task
def process_outbox_events(batch_size: int = 100) -> None:
    """Processes events from the Outbox table."""
    logger.info("Starting to process outbox events", batch_size=batch_size)

    # Filter unprocessed events from the EventOutbox table
    unprocessed_events = EventOutbox.objects.filter(processed=False)[:batch_size]
    if not unprocessed_events.exists():
        logger.info("No unprocessed events found")
        return

    events_to_insert = []
    for event in unprocessed_events:
        events_to_insert.append({
            'event_type': event.event_type,
            'event_date_time': event.event_date_time,
            'environment': event.environment,
            'event_context': event.event_context,
            'metadata_version': event.metadata_version,
        })

    # Log the number of events to be inserted into ClickHouse
    logger.info(f"Inserting {len(events_to_insert)} events into ClickHouse")

    # Insert the events into ClickHouse
    with EventLogClient.init() as client:
        client.insert(events_to_insert)

    # Log the successful insertion
    logger.info(f"Inserted {len(events_to_insert)} events into ClickHouse")

    # Mark events as processed
    EventOutbox.objects.filter(id__in=unprocessed_events).update(
        processed=True, processed_at=now(),
    )

    # Log the completion of processing
    logger.info(f"Marked {len(unprocessed_events)} events as processed")
