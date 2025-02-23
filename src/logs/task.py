from celery import shared_task
from django.conf import settings
from clickhouse_driver import Client as ClickHouseClient
import structlog
from sentry_sdk import capture_exception

from .models import EventLogOutbox

logger = structlog.get_logger(__name__)

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 5},
    retry_backoff=True,
    retry_backoff_max=600,
)
def process_outbox_batch(self):
    batch_size = settings.EVENT_PROCESSING_BATCH_SIZE
    events = list(EventLogOutbox.objects.order_by('created_at')[:batch_size])
    if not events:
        logger.info("no_events_to_process")
        return

    try:
        client = ClickHouseClient(
            host=settings.CLICKHOUSE_HOST,
            port=settings.CLICKHOUSE_PORT,
            user=settings.CLICKHOUSE_USER,
            password=settings.CLICKHOUSE_PASSWORD,
            database=settings.CLICKHOUSE_DB,
        )

        data = [
            (
                event.id,
                event.event_type,
                event.event_date_time,
                event.environment,
                event.event_context,
                event.metadata_version,
            )
            for event in events
        ]

        client.execute(
            "INSERT INTO event_logs (event_type, event_date_time, environment, event_context, metadata_version) VALUES",
            data,
        )

        EventLogOutbox.objects.filter(id__in=[event.id for event in events]).delete()
        logger.info("batch_processed_successfully", batch_size=len(events))

    except Exception as e:
        logger.error("batch_processing_failed", error=str(e))
        capture_exception(e)
        raise self.retry(exc=e)