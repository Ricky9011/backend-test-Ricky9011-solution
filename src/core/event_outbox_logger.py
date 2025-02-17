import inflection
import structlog
from clickhouse_connect.driver.exceptions import DatabaseError
from django.conf import settings

from core.base_model import Model
from core.models import EventOutbox

logger = structlog.get_logger(__name__)


class EventOutboxLogger:

    @classmethod
    def insert(cls, data: list[Model]) -> None:
        try:
            EventOutbox.objects.bulk_create(
                cls._convert_data(data),
            )
        except DatabaseError as e:
            logger.error('unable to insert data to clickhouse', error=str(e))
            raise e

    @staticmethod
    def _convert_data(data: list[Model]) -> list[EventOutbox]:
        return [
            EventOutbox(
                event_type=inflection.underscore(event.__class__.__name__),
                environment=settings.ENVIRONMENT,
                event_context=event.model_dump_json(),
            )
            for event in data
        ]
