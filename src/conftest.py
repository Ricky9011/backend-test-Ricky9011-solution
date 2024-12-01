from typing import Generator

import clickhouse_connect
import pytest
from clickhouse_connect.driver import Client
from django.conf import settings

from log_manager.models import OutboxEvent
from users.use_cases.create_user import UserCreated


@pytest.fixture(scope="module")
def f_ch_client() -> Generator[Client]:
    client = clickhouse_connect.get_client(host="clickhouse")
    yield client
    client.close()


@pytest.fixture(autouse=True)
def f_clean_up_event_log(f_ch_client: Client) -> Generator:
    f_ch_client.query(f"TRUNCATE TABLE {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}")
    yield


TEST_EMAIL = "test@gmail.com"
TEST_FIRST_NAME = "Ivan"
TEST_LAST_NAME = "Ivanov"


@pytest.fixture
def f_sample_outbox_events(db):
    events = [
        OutboxEvent.objects.create(
            event_type="user_created",
            environment="test",
            event_context=UserCreated(
                email=TEST_EMAIL, first_name=TEST_FIRST_NAME, last_name=TEST_LAST_NAME
            ).model_dump_json(),
            status=OutboxEvent.ProcessedStatus.PENDING,
        ),
        OutboxEvent.objects.create(
            event_type="user_created",
            environment="test",
            event_context=UserCreated(
                email="test1@gmail.com", first_name="Igor", last_name="Petrov"
            ).model_dump_json(),
            status=OutboxEvent.ProcessedStatus.PROCESSED,
        ),
    ]
    return events
