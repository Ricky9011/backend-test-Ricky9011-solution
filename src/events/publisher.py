import datetime as dt

import structlog
from django.db import transaction
from django.db.models import QuerySet

from core.base_model import Model
from core.event_log_client import EventLogClient, EventLogClientProtocol
from events.models import EventOutbox

logger = structlog.get_logger(__name__)


class PublishedEvent(Model):
    event_type: str
    event_date_time: dt.datetime
    environment: str
    event_context: str


class EventPublisher:
    """Publish events to Clickhouse (or any other storage)

    Retrieve all not sent events from event outbox, then try to send them
    right to the storage with mark events as sent if succeed

    Setup event client with class attribute EVENT_CLIENT for any client swapping in the future
    """
    EVENT_CLIENT: EventLogClientProtocol = EventLogClient

    @classmethod
    @transaction.atomic()
    def publish(cls) -> None:
        db_events = cls._get_db_events()
        events_models = cls._get_events_models(db_events)
        cls._mark_events_as_sent(db_events)
        cls._insert_events(events_models)

    @classmethod
    def _get_db_events(cls) -> QuerySet[EventOutbox]:
        logger.info('getting all not sent events')
        return EventOutbox.objects.filter(is_sent=False)

    @classmethod
    def _get_events_models(cls, db_events: QuerySet[EventOutbox]) -> list[PublishedEvent]:
        return [
            PublishedEvent(
                event_type=db_event.event_type,
                event_date_time=db_event.created_at,
                environment=db_event.environment,
                event_context=db_event.event_context,
            ) for db_event in db_events
        ]

    @classmethod
    def _mark_events_as_sent(cls, db_events: QuerySet[EventOutbox]) -> None:
        for db_event in db_events:
            db_event.is_sent = True
        EventOutbox.objects.bulk_update(db_events, ['is_sent'])

    @classmethod
    def _insert_events(cls, events: list[PublishedEvent]) -> None:
        with cls.EVENT_CLIENT.init() as client:
            client.insert(events)
