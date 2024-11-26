
import structlog

from core.base_model import Model
from core.services.event_service import EventService
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
    def _execute(self, request: CreateUserRequest) -> CreateUserResponse:
        logger.info('creating a new user')

        user, created = User.objects.get_or_create(
            email=request.email,
            defaults={
                'first_name': request.first_name,
                'last_name': request.last_name,
            },
        )

        if created:
            logger.info('user has been created')
            # Publishing event using the new service instead of direct ClickHouse insertion
            EventService.publish_event(
                event_type='user_created',
                event_data={
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                },
            )
            return CreateUserResponse(result=user)

        logger.error('unable to create a new user')
        return CreateUserResponse(error='User with this email already exists')
