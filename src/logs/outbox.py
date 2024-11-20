from django.conf import settings
from django.utils import timezone
from pydantic import BaseModel

from src.common.utils import to_snake_case
from src.logs.models import OutboxLog


class OutboxLogger:
    @classmethod
    def log(cls, data: list[BaseModel]) -> None:
        OutboxLog.objects.bulk_create(
            [
                OutboxLog(
                    event_type=to_snake_case(event.__class__.__name__),
                    event_date_time=timezone.now(),
                    environment=settings.ENVIRONMENT,
                    event_context=event.model_dump_json(),
                    metadata_version=settings.METADATA_VERSION,
                )
                for event in data
            ],
        )
