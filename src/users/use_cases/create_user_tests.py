import uuid
from collections.abc import Generator

import pytest
from clickhouse_connect.driver import Client
from django.conf import settings

from core.models import EventOutbox
from users.use_cases import CreateUser, CreateUserRequest, UserCreated

pytestmark = [pytest.mark.django_db]


@pytest.fixture()
def f_use_case() -> CreateUser:
    return CreateUser()


@pytest.fixture(autouse=True)
def f_clean_up_event_log(f_ch_client: Client) -> Generator:
    f_ch_client.query(f'TRUNCATE TABLE {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}')
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


# Edited this test to check EventOutbox instead of ClickHouse
def test_event_log_entry_published(f_use_case: CreateUser) -> None:
    email = f'test_{uuid.uuid4()}@email.com'
    request = CreateUserRequest(
        email=email, first_name='Test', last_name='Testovich',
    )

    # Add an event to EventOutbox
    f_use_case.execute(request)

    # Check if the new entry exists in EventOutbox
    outbox_entry = EventOutbox.objects.filter(
        event_type='user_created',
        event_context=UserCreated(email=email, first_name='Test', last_name='Testovich').model_dump_json(),
    ).first()

    # Assert that the event was logged in EventOutbox
    assert outbox_entry is not None
    assert outbox_entry.event_type == 'user_created'
    assert outbox_entry.environment == 'Local'
    assert outbox_entry.metadata_version == 1
