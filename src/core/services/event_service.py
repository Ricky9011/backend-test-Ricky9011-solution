# src/core/services/event_service.py

from django.db import transaction

from core.models import OutboxEvent
from core.observability import trace_event


class EventPublishError(Exception):
    """Custom exception for event publishing errors"""
    pass

class EventService:
    @staticmethod
    @transaction.atomic
    @trace_event("publish_event")
    def publish_event(event_type: str, event_data: dict) -> None:
        """
        Publishes an event by saving it to the outbox table.
        Uses transaction to ensure data consistency.

        Args:
            event_type: Type of the event to publish
            event_data: Event payload data

        Raises:
            EventPublishError: If event publishing fails
        """
        try:
            OutboxEvent.objects.create(
                event_type=event_type,
                event_data=event_data,
            )
        except Exception as e:
            raise EventPublishError(f"Failed to publish event: {str(e)}") from e
