from typing import Any

import structlog
from celery import shared_task
from django.conf import settings
from django.db import transaction

from log_manager.utils import (
    convert_event_models_to_ch_data,
    get_ch_client,
    send_events_to_clickhouse,
)

from .models import OutboxEvent

logger = structlog.get_logger(__name__)


# periodic task to write event logs from pg to ch
@shared_task
def process_outbox():
    BATCH_SIZE = settings.CLICKHOUSE_EVENT_INSERT_BATCH_SIZE
    pending_events = OutboxEvent.objects.filter(status=OutboxEvent.ProcessedStatus.PENDING).order_by("created_at")[
        :BATCH_SIZE
    ]
    if not pending_events.exists():
        logger.info("No events to process")
        return
    data = convert_event_models_to_ch_data(pending_events)
    try:
        with transaction.atomic():
            event_ids = list(pending_events.values_list("id", flat=True))
            OutboxEvent.objects.filter(id__in=event_ids).update(status=OutboxEvent.ProcessedStatus.PROCESSED)
            send_events_to_clickhouse(get_ch_client(), data)
        logger.info("Processed events", count=len(data))
    except Exception as e:
        logger.error("Failed to process events", error=str(e))
        raise
