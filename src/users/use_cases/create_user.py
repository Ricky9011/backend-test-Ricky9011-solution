from typing import Any

import structlog

from core.base_model import Model
from outbox.transactional_outbox import TransactionalOutbox
from core.use_case import UseCase, UseCaseRequest, UseCaseResponse
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
    def _get_context_vars(self, request: UseCaseRequest) -> dict[str, Any]:
        return {
            'email': request.email,
            'first_name': request.first_name,
            'last_name': request.last_name,
        }

    def _create_user_logic(self, request: CreateUserRequest):
        user, created = User.objects.get_or_create(
            email=request.email,
            defaults={
                'first_name': request.first_name, 'last_name': request.last_name,
            },
        )

        if created:
            logger.info("User created successfully", user_id=user.id)
            return user

        raise ValueError("User with this email already exists")

    def _execute(self, request: CreateUserRequest) -> CreateUserResponse:
        logger.info('creating a new user')

        try:
            user = TransactionalOutbox.execute_with_event(
                event_type="UserCreated",
                event_payload={
                    "email": request.email,
                    "first_name": request.first_name,
                    "last_name": request.last_name,
                },
                func=self._create_user_logic,
                request=request,
            )
            return CreateUserResponse(result=user)
        except ValueError as e:
            logger.warning("User already exists", email=request.email)
            return CreateUserResponse(error=str(e))
        except Exception as e:
            logger.error("Unexpected error during user creation", exc_info=e)
            return CreateUserResponse(error="Unexpected error occurred")

