import re
from typing import Any

import structlog
from django.conf import settings
from django.db.models import QuerySet
from django.utils import timezone

from core.base_model import Model
from core.event_log_client import EventLogClient
from outbox.models import Outbox

logger = structlog.get_logger(__name__)

class OutboxEventLog:

    def insert_event(self, event: Model) -> None:
        Outbox.objects.create(**self._convert_data(event))

    @staticmethod
    def get_unprocessed_events() -> QuerySet:
        return Outbox.objects.filter(processed_at__isnull=True).order_by('-id')[:settings.CHUNK_SIZE]

    @staticmethod
    def mark_events_as_processed(ids: list[int]) -> None:
        Outbox.objects.filter(id__in=ids).update(processed_at=timezone.now())

    def _convert_data(self, event: Model) -> dict[str, str]:
        return {
            "event_type": self._to_snake_case(event.__class__.__name__),
            "event_date_time": timezone.now(),
            "environment": settings.ENVIRONMENT,
            "event_context": event.model_dump_json(),
        }

    @staticmethod
    def _to_snake_case(event_name: str) -> str:
        result = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', event_name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', result).lower()

class EventProcessor:
    def __init__(self) -> None:
        self.outbox = OutboxEventLog()

    def process_events_chunk(self) -> bool:
        events = self.outbox.get_unprocessed_events()
        if not events.exists():
            return False
        events_ids, data = self._prepare_event_data(events)
        return self._send_events_and_update_status(events_ids, data)

    @staticmethod
    def _prepare_event_data(events: QuerySet) -> (list[int], list[tuple[Any]]):
        events_ids = []
        data = []
        for event in events:
            events_ids.append(event.id)
            data.append(
                (
                    event.event_type,
                    event.event_date_time,
                    event.environment,
                    event.event_context,
                ),
            )
        return events_ids, data

    def _send_events_and_update_status(self, events_ids: list[int], data: list[tuple[Any]]) -> bool:
        try:
            with EventLogClient.init() as client:
                client.insert(data)
            self.outbox.mark_events_as_processed(events_ids)
        except Exception as e:
            logger.error('unable to insert data to clickhouse', error=str(e))
            return False
        return True


outbox_event_log = OutboxEventLog()
