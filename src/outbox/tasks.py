import time

import structlog
from celery import shared_task

from core.sentry import sentry_tracing
from outbox.event_log import EventProcessor

logger = structlog.get_logger(__name__)


@sentry_tracing("ProcessOutboxEvents")
@shared_task
def process_outbox_events() -> None:
    processor = EventProcessor()
    while True:
        try:
            if not processor.process_events_chunk():
                break
        except Exception as e:
            logger.error(f"error processing outbox events: {e}")
            time.sleep(1)
            break
