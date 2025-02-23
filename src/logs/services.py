import structlog
from django.db import transaction
from .models import EventLogOutbox

logger = structlog.get_logger(__name__)

class LogService:
    @staticmethod
    def log_event(event_data: dict):
        try:
            with transaction.atomic():
                EventLogOutbox.objects.create(
                    event_type=event_data['type'],
                    event_date_time=event_data['timestamp'],
                    environment=event_data['env'],
                    event_context=event_data['context'],
                    metadata_version=event_data['version']
                )
                logger.info("Event logged to outbox", event_id=event_data.get('id'))
        except Exception as e:
            logger.error("Failed to log event", error=str(e))
            raise