# core/services.py
import json
from typing import List, Dict, Any
import clickhouse_connect
import structlog
from django.conf import settings
from django.db.models import QuerySet

from core.models import EventOutbox

logger = structlog.get_logger(__name__)

def get_outbox_events(batch_size: int) -> QuerySet[EventOutbox]:
    """Retrieve a batch of events from EventOutbox."""
    return EventOutbox.objects.all()[:batch_size]

def format_events(events: QuerySet[EventOutbox]) -> list[dict[str, Any]]:
    """Format events for ClickHouse insertion."""
    return [
        (
            event.event_type,
            event.event_date_time,
            event.environment,
            json.dumps(event.event_context),
            event.metadata_version,
        )
        for event in events
    ]

def insert_to_clickhouse(data: List[Dict[str, Any]]) -> None:
    """Insert data into ClickHouse."""
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
    finally:
        client.close()
        logger.info("ClickHouse client connection closed")

def delete_processed_events(events: QuerySet[EventOutbox]) -> None:
    """Delete processed events from EventOutbox."""
    EventOutbox.objects.filter(id__in=[event.id for event in events]).delete()
    logger.info("Successfully deleted processed events from EventOutbox")
