import re
from datetime import datetime

import structlog
from django.conf import settings
from django.utils import timezone

from core.base_model import Model
from core.use_case import UseCase, UseCaseRequest, UseCaseResponse
from events.models import EventLog

logger = structlog.get_logger(__name__)


class EventLogCreated(Model):
    event_type: str
    event_date_time: str
    environment: str
    event_context: str


class CreateEventLogRequest(UseCaseRequest):
    event: Model
    
    
class CreateEventLogData(UseCaseRequest):
    event_type: str
    event_date_time: datetime
    environment: str
    event_context: str


class CreateEventLogResponse(UseCaseResponse):
    result: EventLog | None = None
    error: str = ''


class CreateEventLog(UseCase):
    
    def _execute(self, request: CreateEventLogRequest) -> CreateEventLogResponse:
        logger.info('creating a new eventlog')
        event_log_data = self._convert_data(request.event)
        event_log = EventLog.objects.create(**event_log_data.model_dump())
        return CreateEventLogResponse(result=event_log)
    
    def _convert_data(self, event: Model) -> CreateEventLogData:
        return CreateEventLogData(
            event_type=self._to_snake_case(event.__class__.__name__),
            event_date_time=timezone.now(),
            environment=settings.ENVIRONMENT,
            event_context=event.model_dump_json(),
        )

    def _to_snake_case(self, event_name: str) -> str:
        result = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', event_name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', result).lower()
