import time
import uuid
from collections.abc import Generator
from unittest.mock import ANY

import pytest
from clickhouse_connect.driver import Client
from django.conf import settings
from redis import Redis

from core.event_log_client import EventLogClient
from users.use_cases import CreateUser, CreateUserRequest, UserCreated
from users.tasks import log_batch_events

pytestmark = [pytest.mark.django_db]


@pytest.fixture()
def f_use_case() -> CreateUser:
    return CreateUser()


@pytest.fixture(autouse=True)
def f_clean_up_event_log(f_ch_client: Client, f_redis_client: Redis) -> Generator:
    f_ch_client.query(f'TRUNCATE TABLE {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}')
    f_redis_client.delete(EventLogClient.event_log_queue)
    yield


def test_user_created(f_use_case: CreateUser) -> None:
    request = CreateUserRequest(
        email='test@email.com', first_name='Test', last_name='Testovich',
    )

    response = f_use_case.execute(request)

    assert response.result.email == 'test@email.com'
    assert response.error == ''


def test_emails_are_unique(f_use_case: CreateUser) -> None:
    request = CreateUserRequest(
        email='test@email.com', first_name='Test', last_name='Testovich',
    )

    f_use_case.execute(request)
    response = f_use_case.execute(request)

    assert response.result is None
    assert response.error == 'User with this email already exists'


def test_event_log_entry_added_to_queue_and_published(
    f_use_case: CreateUser,
    f_ch_client: Client,
    f_redis_client: Redis
) -> None:
    llen = f_redis_client.llen('event_log_queue')
    email = f'test_{uuid.uuid4()}@email.com'
    f_redis_client.set('test_user_email', email)
    request = CreateUserRequest(
        email=email, first_name='Test', last_name='Testovich',
    )

    f_use_case.execute(request)
    assert f_redis_client.llen(EventLogClient.event_log_queue) == llen + 1
    f_redis_client.set(EventLogClient.event_log_inserted_time_key, -11)
    log_batch_events.apply()
    log = f_ch_client.query("SELECT * FROM default.event_log WHERE event_type = 'user_created'")

    assert log.result_rows == [
        (
            'user_created',
            ANY,
            'Local',
            UserCreated(email=email, first_name='Test', last_name='Testovich').model_dump_json(),
            1,
        ),
    ]
