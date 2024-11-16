from typing import Any

import structlog
from django.db import transaction

from core.base_model import Model
from core.event_log_client import EventLogClient
from core.use_case import UseCase, UseCaseRequest, UseCaseResponse
from events.use_cases.create_events_log import CreateEventLog, CreateEventLogRequest
from users.models import User

logger = structlog.get_logger(__name__)


class UserCreated(Model):
    email: str
    first_name: str
    last_name: str


class CreateUserRequest(UseCaseRequest):
    email: str
    first_name: str = ''
    last_name: str = ''


class CreateUserResponse(UseCaseResponse):
    result: User | None = None
    error: str = ''


class CreateUser(UseCase):
    def _get_context_vars(self, request: CreateUserRequest) -> dict[str, Any]:
        return {
            'email': request.email,
            'first_name': request.first_name,
            'last_name': request.last_name,
        }
    
    @transaction.atomic()
    def _execute(self, request: CreateUserRequest) -> CreateUserResponse:
        logger.info('creating a new user')

        user, created = User.objects.get_or_create(
            email=request.email,
            defaults={
                'first_name': request.first_name, 'last_name': request.last_name,
            },
        )

        if created:
            logger.info('user has been created')
            event_log_request = CreateEventLogRequest(event=self._make_event(user))
            CreateEventLog().execute(event_log_request)
            return CreateUserResponse(result=user)

        logger.error('unable to create a new user')
        return CreateUserResponse(error='User with this email already exists')
    
    def _make_event(self, user: User) -> UserCreated:
        return UserCreated(
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )

