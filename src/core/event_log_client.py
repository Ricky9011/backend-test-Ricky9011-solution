import json
import re
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from typing import Any

import clickhouse_connect
import structlog
from clickhouse_connect.driver.exceptions import DatabaseError
from django.conf import settings
from django.utils import timezone

from core.base_model import Model

logger = structlog.get_logger(__name__)

EVENT_LOG_COLUMNS = [
    'event_type',
    'event_date_time',
    'environment',
    'event_context',
]


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj: datetime | Model) -> str:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class EventLogClient:
    def __init__(self, client: clickhouse_connect.driver.Client) -> None:
        self._client = client

    @classmethod
    @contextmanager
    def init(cls) -> Generator['EventLogClient']:
        client = clickhouse_connect.get_client(
            host=settings.CLICKHOUSE_HOST.strip(),
            port=settings.CLICKHOUSE_PORT,
            user=settings.CLICKHOUSE_USER,
            password=settings.CLICKHOUSE_PASSWORD,
            query_retries=5,
            connect_timeout=60,
            send_receive_timeout=30,
        )
        try:
            yield cls(client)
        except Exception as e:
            logger.error('error while executing clickhouse query', error=str(e))
        finally:
            client.close()

    def insert(
        self,
        data: list[tuple[Any, ...]],
        column_names: list[str],
        table: str = settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME,
    ) -> None:
        try:
            self._client.insert(
                table=table,
                data=data,
                column_names=column_names,
            )
        except DatabaseError as e:
            logger.error('unable to insert data to clickhouse', error=str(e))

    def query(self, query: str) -> Any:  # noqa: ANN401
        logger.debug('executing clickhouse query', query=query)

        try:
            return self._client.query(query).result_rows
        except DatabaseError as e:
            logger.error('failed to execute clickhouse query', error=str(e))
            return

    def _convert_data(self, data: list[dict | Model]) -> list[tuple[Any]]:
        """
        Convert input data to format suitable for ClickHouse.
        Handles both Pydantic models and dictionaries.
        """
        def get_json_data(event: dict | Model) -> str:
            if isinstance(event, dict):
                return json.dumps(event, cls=DateTimeEncoder)
            return event.model_dump_json()

        return [
            (
                self._to_snake_case(
                    event.__class__.__name__ if isinstance(event, Model) else 'dict',
                ),
                timezone.now(),
                settings.ENVIRONMENT,
                get_json_data(event),
            )
            for event in data
        ]

    def _to_snake_case(self, event_name: str) -> str:
        result = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', event_name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', result).lower()

