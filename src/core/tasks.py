import structlog
from celery import shared_task
from django.db.models import QuerySet
from sentry_sdk import capture_exception

from core.models import EventOutbox
from core.services import delete_processed_events, format_events, get_outbox_events, insert_to_clickhouse

logger = structlog.get_logger(__name__)

@shared_task
def process_event_outbox(batch_size: int = 10) -> None:
    while True:
        events = get_outbox_events(batch_size)
        if not events:
            logger.info("No more events to process")
            break

        if not process_and_log_events(events):
            break  # Stop processing if there's an error

def process_and_log_events(events: QuerySet[EventOutbox]) -> bool:
    """Process events by formatting, inserting to ClickHouse, and deleting."""
    try:
        data = format_events(events)
        insert_to_clickhouse(data)
        delete_processed_events(events)
        return True
    except Exception as e:
        handle_insertion_error(e)
        return False

def handle_insertion_error(exception: Exception) -> None:
    """Handle errors during insertion, logging and capturing exceptions."""
    logger.error("Error inserting events to ClickHouse")
    try:
        capture_exception(exception)
    except Exception:
        logger.error("Failed to capture exception with Sentry")
