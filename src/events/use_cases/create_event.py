import re
from typing import Any

import structlog
from django.conf import settings
from django.db import DatabaseError

from core.base_model import Model
from core.use_case import UseCase, UseCaseRequest
from events.models import EventOutbox

logger = structlog.get_logger(__name__)


class EventCreated(Model):
    event_type: str
    environment: str
    event_context: str


class CreateEventRequest(UseCaseRequest):
    event_type: str
    environment: str
    event_context: str


class CreateEvent(UseCase):

    def __init__(self, event_object: Model) -> None:
        self._event_object = event_object

    def _get_context_vars(self, request: UseCaseRequest) -> dict[str, Any]:
        return {
            'event_type': request.event_type,
            'environment': request.environment,
            'event_context': request.event_context,
        }

    def _execute(self, request: CreateEventRequest) -> None:
        logger.info('creating a new event')

        try:
            EventOutbox.objects.create(
                event_type=request.event_type,
                environment=request.environment,
                event_context=request.event_context,
            )
        except DatabaseError:
            logger.error('unable to create a new event')
            raise

    def _convert_event_object_to_request(self) -> CreateEventRequest:
        return CreateEventRequest(
            event_type=self._to_snake_case(self._event_object.__class__.__name__),
            environment=settings.ENVIRONMENT,
            event_context=self._event_object.model_dump_json(),
        )

    def _to_snake_case(self, event_name: str) -> str:
        result = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', event_name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', result).lower()

    def create(self) -> None:
        request = self._convert_event_object_to_request()
        return self._execute(request)

