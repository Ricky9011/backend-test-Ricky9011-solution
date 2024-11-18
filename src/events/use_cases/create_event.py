import re

import structlog
from django.conf import settings
from django.db import DatabaseError

from core.base_model import Model
from core.use_case import UseCase, UseCaseRequest, UseCaseResponse
from events.models import EventOutbox

logger = structlog.get_logger(__name__)


class EventCreated(Model):
    event_type: str
    environment: str
    event_context: str


class CreateEventRequestData(Model):
    event_type: str
    environment: str
    event_context: str


class ProcessedEventRequest(UseCaseRequest):
    events_data: list[CreateEventRequestData]


class CreateEventRequest(UseCaseRequest):
    raw_data: list[Model]


class CreateEvent(UseCase):
    """UseCase for event creation.

    Passed arguments:
    - event_objects: list[Model] - list of Base model successors from which we try to obtain events

    Try to get events data from list of Model objects and write them to db in batch.

    !!! This UseCase intended to be used inside an outer transaction.atomic block created by caller
    who execute CreateEvent for db consistency therefore it just raises db exception without any processing
    """

    def _execute(self, request: ProcessedEventRequest) -> None:
        logger.info('creating a new event')

        events = [EventOutbox(
            event_type=event.event_type,
            environment=event.environment,
            event_context=event.event_context,
        ) for event in request.events_data]
        try:
            EventOutbox.objects.bulk_create(events, batch_size=1000)
        except DatabaseError:
            logger.error('unable to create a new event')
            raise

    def _convert_event_objects_to_request(self, request: CreateEventRequest) -> ProcessedEventRequest:
        return ProcessedEventRequest(events_data=[
            CreateEventRequestData(
                event_type=self._to_snake_case(event_object.__class__.__name__),
                environment=settings.ENVIRONMENT,
                event_context=event_object.model_dump_json(),
            )
            for event_object in request.raw_data
        ])

    def _to_snake_case(self, event_name: str) -> str:
        result = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', event_name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', result).lower()

    def execute(self, request: CreateEventRequest) -> UseCaseResponse:
        processed_request = self._convert_event_objects_to_request(request)
        self._execute(processed_request)
        return UseCaseResponse()

