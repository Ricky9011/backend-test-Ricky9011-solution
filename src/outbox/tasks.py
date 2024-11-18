from celery import shared_task
from outbox.event_log_processor import EventLogProcessor
from core.event_log_client import EventLogClient
import structlog

logger = structlog.get_logger(__name__)


@shared_task
def process_outbox_task(batch_size: int = 100):
    try:
        with EventLogClient.init() as client:
            processor = EventLogProcessor(clickhouse_client=client, batch_size=batch_size)
            processor.process_events()
    except Exception as e:
        logger.error("Failed to process event logs", exc_info=e)
