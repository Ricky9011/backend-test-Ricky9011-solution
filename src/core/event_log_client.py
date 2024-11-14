import re
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import clickhouse_connect
import structlog
from clickhouse_connect.driver.exceptions import DatabaseError
from django.conf import settings
from django.utils import timezone

from core.base_model import Model
from core.models import EventOutbox  # Import the EventOutbox model

logger = structlog.get_logger(__name__)

EVENT_LOG_COLUMNS = [
    'event_type',
    'event_date_time',
    'environment',
    'event_context',
]


class EventLogClient:
    def __init__(self, client: clickhouse_connect.driver.Client) -> None:
        self._client = client

    @classmethod
    @contextmanager
    def init(cls) -> Generator['EventLogClient']:
        client = clickhouse_connect.get_client(
            host=settings.CLICKHOUSE_HOST,
            port=settings.CLICKHOUSE_PORT,
            user=settings.CLICKHOUSE_USER,
            password=settings.CLICKHOUSE_PASSWORD,
            query_retries=2,
            connect_timeout=30,
            send_receive_timeout=10,
        )
        try:
            yield cls(client)
        except Exception as e:
            logger.error('error while executing clickhouse query', error=str(e))
        finally:
            client.close()

    def insert(
        self,
        data: list[Model],
    ) -> None:

        # Instead of inserting directly into clickhouse, save to EventOutbox
        try:
            for event in data:
                EventOutbox.objects.create(
                    event_type=self._to_snake_case(event.__class__.__name__),
                    event_date_time=timezone.now(),
                    environment=settings.ENVIRONMENT,
                    event_context=event.model_dump_json(),  # JSON data
                    metadata_version=1,  # Set appropriate version
                )
            logger.info("Events successfully saved to EventOutbox for async processing")
        except DatabaseError as e:
            logger.error('unable to save event to outbox', error=str(e))

    def query(self, query: str) -> Any:  # noqa: ANN401
        logger.debug('executing clickhouse query', query=query)

        try:
            return self._client.query(query).result_rows
        except DatabaseError as e:
            logger.error('failed to execute clickhouse query', error=str(e))
            return

    def _convert_data(self, data: list[Model]) -> list[tuple[Any]]:
        return [
            (
                self._to_snake_case(event.__class__.__name__),
                timezone.now(),
                settings.ENVIRONMENT,
                event.model_dump_json(),
            )
            for event in data
        ]

    def _to_snake_case(self, event_name: str) -> str:
        result = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', event_name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', result).lower()

