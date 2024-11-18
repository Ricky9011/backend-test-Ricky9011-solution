from django.utils.timezone import now
from core.event_log_client import EventLogClient
import structlog

from outbox.models import EventLogOutbox

logger = structlog.get_logger(__name__)


class EventLogProcessor:
    def __init__(self, clickhouse_client: EventLogClient, batch_size: int = 100):
        self.clickhouse_client = clickhouse_client
        self.batch_size = batch_size

    def process_events(self):
        while True:
            events = EventLogOutbox.objects.filter(processed_at__isnull=True)[:self.batch_size]
            if not events.exists():
                logger.info("No more events to process")
                break

            data = [
                {
                    "event_type": event.event_type,
                    "event_date_time": event.created_at.isoformat(),
                    "environment": self.clickhouse_client.environment,
                    "event_context": event.payload,
                }
                for event in events
            ]

            try:
                self.clickhouse_client.insert(data=data)
                events.update(processed_at=now())
                logger.info("Processed batch of events", count=len(events))
            except Exception as e:
                logger.error("Error processing events", exc_info=e)
                break
