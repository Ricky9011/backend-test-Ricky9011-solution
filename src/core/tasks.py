from celery import shared_task
import structlog

from src.core.services import EventLogService

logger = structlog.get_logger(__name__)


@shared_task
def send_event_logs():
    service = EventLogService()
    service.send_unprocessed_logs()

