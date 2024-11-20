from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from pydantic import BaseModel

from src.common.utils import to_snake_case
from src.logs.ch_client import ClickHouseClient
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


class OutboxExporter:
    @classmethod
    def export(cls) -> None:
        while True:
            with transaction.atomic():
                objs = (
                    OutboxLog.objects.filter(exported_at__isnull=True)
                    .select_for_update()
                    .order_by("id")[: settings.CLICKHOUSE_BATCH_SIZE]
                )
                if not objs:
                    return

                data = cls._convert_data(objs)

                client: ClickHouseClient
                with ClickHouseClient.init() as client:
                    client.insert(data)

                OutboxLog.objects.filter(id__in=[obj.id for obj in objs]).update(
                    exported_at=timezone.now(),
                )

    @staticmethod
    def _convert_data(
        data: list[OutboxLog],
    ) -> list[tuple[str, datetime, str, str, int]]:
        return [
            (
                event.event_type,
                event.event_date_time,
                event.environment,
                event.event_context,
                event.metadata_version,
            )
            for event in data
        ]

    @staticmethod
    def cleanup() -> None:
        bound = timezone.now() - timedelta(seconds=settings.CLICKHOUSE_CLEANUP_INTERVAL)
        OutboxLog.objects.filter(exported_at__lt=bound).delete()
