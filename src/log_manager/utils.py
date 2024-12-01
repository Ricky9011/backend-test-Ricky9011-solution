from typing import Any, Iterable

import clickhouse_connect
from django.conf import settings

from log_manager.models import OutboxEvent

EVENT_LOG_COLUMNS = ["event_type", "event_date_time", "environment", "event_context", "metadata_version"]


def send_events_to_clickhouse(client: clickhouse_connect.driver.Client, data: list[tuple[Any]]):
    client.insert(
        data=data,
        column_names=EVENT_LOG_COLUMNS,
        database=settings.CLICKHOUSE_SCHEMA,
        table=settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME,
    )


def get_ch_client() -> clickhouse_connect.driver.Client:
    return clickhouse_connect.get_client(
        host=settings.CLICKHOUSE_HOST,
        port=settings.CLICKHOUSE_PORT,
        user=settings.CLICKHOUSE_USER,
        password=settings.CLICKHOUSE_PASSWORD,
        query_retries=2,
        connect_timeout=30,
        send_receive_timeout=10,
    )


def convert_event_models_to_ch_data(pending_events: Iterable[OutboxEvent]) -> list[tuple[Any]]:
    return [
        (
            event.event_type,
            event.created_at,
            event.environment,
            event.event_context,
            event.metadata_version,
        )
        for event in pending_events
    ]
