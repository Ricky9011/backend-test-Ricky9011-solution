# core/tasks.py
import json
import logging

import clickhouse_connect
from celery import shared_task
from django.conf import settings

from core.models import EventOutbox

logger = logging.getLogger(__name__)


@shared_task
def process_event_outbox() -> None:
    logger.info("Starting process_event_outbox task")

    # Retrieve events in batches of 10
    events = EventOutbox.objects.all()[:10]

    if not events:
        logger.info("No events to process")
        return

    logger.info(f"Retrieved {len(events)} events from EventOutbox")

    # Format data for clickhouse insert
    data = [
        (
            event.event_type,
            event.event_date_time,
            event.environment,
            json.dumps(event.event_context),
            event.metadata_version,
        )
        for event in events
    ]

    # Connect to clickhouse and insert data
    client = clickhouse_connect.get_client(
        host=settings.CLICKHOUSE_HOST,
        port=settings.CLICKHOUSE_PORT,
        user=settings.CLICKHOUSE_USER,
        password=settings.CLICKHOUSE_PASSWORD,
    )
    try:
        client.insert(
            data=data,
            column_names=['event_type', 'event_date_time', 'environment', 'event_context', 'metadata_version'],
            database=settings.CLICKHOUSE_SCHEMA,
            table=settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME,
        )
        logger.info(f"Successfully inserted {len(data)} events to ClickHouse")

        # Delete the events after successful insertion to Clickhouse
        EventOutbox.objects.filter(id__in=[event.id for event in events]).delete()
        logger.info("Successfully deleted processed events from EventOutbox")

    except Exception as e:
        # Log an error if insertion fails
        logger.error(f"Error inserting events to ClickHouse: {e}")

        # Capture exception without raising pickling errors
        try:
            from sentry_sdk import capture_exception
            capture_exception(e)
        except Exception as capture_err:
            # Log the error directly in the message without using a keyword argument
            logger.error(f"Failed to capture exception with Sentry: {capture_err}")

    finally:
        client.close()
        logger.info("ClickHouse client connection closed")
