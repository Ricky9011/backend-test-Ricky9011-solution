import re
import json
import time

from redis import Redis, ConnectionPool
from collections.abc import Generator
from contextlib import contextmanager
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


class EventLogClient:
    event_log_queue = "event_log_queue"
    failed_events_queue = "failed_events_queue"
    event_log_inserted_time_key = "event_log_inserted_time"

    def __init__(self, clickhouse_client: clickhouse_connect.driver.Client, redis_client: Redis,
                 batch_size: int = settings.CLICKHOUSE_BATCH_SIZE,
                 batch_timeout: int = settings.CLICKHOUSE_BATCH_INSERTION_TIMEOUT) -> None:
        self._clickhouse_client = clickhouse_client
        self._redis_client = redis_client
        self._batch_size = batch_size
        self._batch_timeout = batch_timeout

    @classmethod
    @contextmanager
    def init(cls) -> Generator['EventLogClient']:
        clickhouse_client = clickhouse_connect.get_client(
            host=settings.CLICKHOUSE_HOST,
            port=settings.CLICKHOUSE_PORT,
            user=settings.CLICKHOUSE_USER,
            password=settings.CLICKHOUSE_PASSWORD,
            query_retries=2,
            connect_timeout=30,
            send_receive_timeout=10,
        )
        pool = ConnectionPool(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, decode_responses=True)
        redis_client = Redis(connection_pool=pool)
        try:
            yield cls(clickhouse_client, redis_client)
        except Exception as e:
            logger.error('error while executing clickhouse query', error=str(e))
        finally:
            clickhouse_client.close()
            redis_client.close()

    def log_event(self, data: list[Model]):
        """Sends event to redis queue and stores it here, until it will send to ClickHouse."""
        try:
            for event in self._convert_data_to_redis(data):
                self._redis_client.lpush(self.event_log_queue, json.dumps(event))
        except Exception as e:
            logger.error('error while writing events to redis', error=str(e))

    def need_to_consume_events(self):
        """Checks, do we need to consume events from redis and send it to ClickHouse?"""
        return self._redis_client.llen(self.event_log_queue) >= self._batch_size or \
            time.monotonic() - float(self._redis_client.get(self.event_log_inserted_time_key) or 0) > self._batch_timeout

    def consume_events(self, send_failed: bool = False):
        """Consumes events from redis and sends them to ClickHouse."""
        batch = []
        raw_batch = []
        queue_name = self.failed_events_queue if send_failed else self.event_log_queue
        while True:
            event = self._redis_client.rpop(queue_name)
            if event:
                raw_batch.append(event)
                serialized_event = json.loads(event)
                batch.append((serialized_event['event_type'], timezone.datetime.fromisoformat(serialized_event['event_date_time']),
                              serialized_event['environment'], serialized_event['event_context']))
            else:
                break

        try:
            self.batch_insert(batch)
            logger.info(f'batch inserted, size={len(batch)}')
            self._redis_client.set(self.event_log_inserted_time_key, time.monotonic())
        except Exception as e:
            if not send_failed:
                for raw_event in raw_batch:
                    self._redis_client.lpush(self.failed_events_queue, raw_event)
            else:
                logger.error(f'Couldn\'t resend failed events', error=f'{batch}')
            logger.error('error while consume events', error=str(e))

    def insert(
        self,
        data: list[Model],
    ) -> None:
        self._insert(self._convert_data_to_clickhouse(data))

    def batch_insert(self, batch: list[tuple]):
        self._insert(batch)

    def _insert(self, data: list):
        try:
            self._clickhouse_client.insert(
                data=data,
                column_names=EVENT_LOG_COLUMNS,
                database=settings.CLICKHOUSE_SCHEMA,
                table=settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME,
            )
        except DatabaseError as e:
            logger.error('unable to insert batch data to clickhouse', error=str(e))
            raise e

    def query(self, query: str) -> Any:  # noqa: ANN401
        logger.debug('executing clickhouse query', query=query)

        try:
            return self._clickhouse_client.query(query).result_rows
        except DatabaseError as e:
            logger.error('failed to execute clickhouse query', error=str(e))
            return

    def _convert_data_to_clickhouse(self, data: list[Model]) -> list[tuple[Any]]:
        return [
            (
                self._to_snake_case(event.__class__.__name__),
                timezone.now(),
                settings.ENVIRONMENT,
                event.model_dump_json(),
            )
            for event in data
        ]

    def _convert_data_to_redis(self, data: list[Model]) -> list[dict[str, Any]]:
        return [
            {
                "event_type": self._to_snake_case(event.__class__.__name__),
                "event_date_time": timezone.now().isoformat(),
                "environment": settings.ENVIRONMENT,
                "event_context": event.model_dump_json(),
            } for event in data
        ]

    def _to_snake_case(self, event_name: str) -> str:
        result = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', event_name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', result).lower()

