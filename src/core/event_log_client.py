import re
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import structlog
from clickhouse_connect.driver.exceptions import DatabaseError
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.base_model import Model
from log_manager.models import OutboxEvent

logger = structlog.get_logger(__name__)


class EventLogClient:

    @classmethod
    @contextmanager
    def init(cls) -> Generator["EventLogClient"]:
        yield cls()

    def insert(
        self,
        data: list[Model],
    ) -> None:
        if not transaction.get_connection().in_atomic_block:
            logger.error(
                "insert_called_outside_transaction", in_atomic_block=transaction.get_connection().in_atomic_block
            )
            raise RuntimeError("EventLogClient.insert must be called within a transaction.atomic block")

        try:
            OutboxEvent.objects.bulk_create(self._convert_data(data))
        except DatabaseError as e:
            logger.error("unable to insert data to outbox", error=str(e))
            raise

    def _convert_data(self, data: list[Model]) -> list[OutboxEvent]:
        return [
            OutboxEvent(
                event_type=self._to_snake_case(event.__class__.__name__),
                environment=settings.ENVIRONMENT,
                event_context=event.model_dump_json(),
            )
            for event in data
        ]

    def _to_snake_case(self, event_name: str) -> str:
        result = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", event_name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", result).lower()
