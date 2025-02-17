import re

import structlog
from django.conf import settings
from django.utils import timezone

from core.base_model import Model
from core.models import OutboxEvent


def _to_snake_case(name: str) -> str:
    result = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", result).lower()


logger = structlog.get_logger(__name__)


def publish_event(event: Model) -> None:
    event_type = _to_snake_case(event.__class__.__name__)

    logger.info("Publishing event", event_type=event_type, event_data=event.model_dump())

    try:
        OutboxEvent.objects.create(
            event_type=event_type,
            event_date_time=timezone.now(),
            environment=settings.ENVIRONMENT,
            event_context=event.model_dump(),
            processed=False,
        )
        logger.info("Event successfully published", event_type=event_type)
    except Exception as e:
        logger.error("Failed to publish event", event_type=event_type, error=str(e))
