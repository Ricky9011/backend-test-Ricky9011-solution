import uuid
from collections.abc import Generator
from unittest.mock import ANY

import pytest
from clickhouse_connect.driver import Client
from django.conf import settings
from django.db.backends.base.base import BaseDatabaseWrapper

from outbox.event_log import EventProcessor, OutboxEventLog
from users.use_cases import CreateUser, CreateUserRequest, UserCreated


@pytest.fixture(autouse=True)
def f_clean_up_databases(f_ch_client: Client, f_pg_client: BaseDatabaseWrapper) -> Generator:
    f_ch_client.query(f"TRUNCATE TABLE {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}")

    with f_pg_client.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE outbox_outbox RESTART IDENTITY CASCADE")
        f_pg_client.commit()

    yield


@pytest.fixture()
def outbox_event_log() -> OutboxEventLog:
    return OutboxEventLog()


@pytest.fixture()
def f_processor_case() -> EventProcessor:
    return EventProcessor()


@pytest.mark.django_db(transaction=True)
def test_insert_event(
    f_ch_client: Client,
    f_processor_case: EventProcessor,
    f_use_case: CreateUser,
) -> None:
    email = f'test_{uuid.uuid4()}@email.com'
    request = CreateUserRequest(
        email=email, first_name='Test', last_name='Testovich',
    )
    f_use_case.execute(request)
    result = f_processor_case.outbox.get_unprocessed_events()
    assert result.exists()

    f_processor_case.process_events_chunk()
    result = f_processor_case.outbox.get_unprocessed_events()
    assert not result.exists()

    log = f_ch_client.query("SELECT * FROM default.buffer_event_log WHERE event_type = 'user_created'")
    assert log.result_rows == [
        (
            'user_created',
            ANY,
            'Local',
            UserCreated(email=email, first_name='Test', last_name='Testovich').model_dump_json(),
            1,
        ),
    ]



