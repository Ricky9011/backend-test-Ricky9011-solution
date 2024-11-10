from typing import Any

import structlog
from django.db.utils import IntegrityError

from core.base_model import Model
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

    def _execute(self, request: CreateUserRequest) -> CreateUserResponse:
        logger.info('creating a new user')

        try:
            user = User.objects.create(
                email=request.email,
                first_name=request.first_name,
                last_name=request.last_name,
            )
            logger.info('user has been created')
            return CreateUserResponse(result=user)
        except IntegrityError:
            logger.error('unable to create a new user as it already exists')
            return CreateUserResponse(error='User with this email already exists')

        logger.error('unable to create a new user')
        return CreateUserResponse(error='Unknown error while creating a new user')
