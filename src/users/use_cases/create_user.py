from typing import Any

import structlog
from django.db import transaction

from src.common.model import PydanticModel
from src.common.use_case import UseCase, UseCaseRequest, UseCaseResponse
from src.logs.outbox import OutboxLogger
from src.users.models import User

logger = structlog.get_logger(__name__)


class UserCreated(PydanticModel):
    email: str
    first_name: str
    last_name: str


class CreateUserRequest(UseCaseRequest):
    email: str
    first_name: str = ""
    last_name: str = ""


class CreateUserResponse(UseCaseResponse):
    result: User | None = None
    error: str = ""


class CreateUser(UseCase):
    def _get_context_vars(self, request: UseCaseRequest) -> dict[str, Any]:
        return {
            "email": request.email,
            "first_name": request.first_name,
            "last_name": request.last_name,
        }

    @transaction.atomic
    def _execute(self, request: CreateUserRequest) -> CreateUserResponse:
        logger.info("creating a new user")

        user, created = User.objects.get_or_create(
            email=request.email,
            defaults={
                "first_name": request.first_name,
                "last_name": request.last_name,
            },
        )

        if not created:
            logger.error("unable to create a new user")
            return CreateUserResponse(error="User with this email already exists")

        logger.info("user has been created")
        self._log(user)

        return CreateUserResponse(result=user)

    def _log(self, user: User) -> None:
        data = [
            UserCreated(
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
            ),
        ]
        OutboxLogger.log(data)
