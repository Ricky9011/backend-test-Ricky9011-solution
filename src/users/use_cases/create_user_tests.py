import json
import uuid
from collections.abc import Generator

import pytest
from clickhouse_connect.driver import Client
from django.conf import settings

from outbox_pattern.models import EventOutbox
from outbox_pattern.tasks import process_outbox_events
from users.use_cases import CreateUser, CreateUserRequest

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


def test_event_log_entry_published(
    f_use_case: CreateUser,
    f_ch_client: Client,
) -> None:
    email = f"test_{uuid.uuid4()}@email.com"
    request = CreateUserRequest(
        email=email, first_name='Test', last_name='Testovich',
    )

    f_use_case.execute(request)

    # Trigger the process to handle events from EventBox and insert them into ClickHouse
    process_outbox_events()

    # Query ClickHouse to retrieve events with the 'user has been created' event type
    log = f_ch_client.query(
        "SELECT * FROM default.event_log WHERE event_type = 'user has been created'",
    )

    # Assert that exactly one event was found in ClickHouse
    assert len(log.result_rows) == 1

    selected_row = log.result_rows[0]
    selected_row_context = json.loads(selected_row[3])

    right_event_context = {
        "email": email,
        "first_name": "Test",
        "last_name": "Testovich",
    }

    # Verify that the context of the log matches the expected event data
    assert selected_row_context == right_event_context


def test_event_created_outbox(f_use_case: CreateUser) -> None:
    email = "test@example.com"
    request = CreateUserRequest(
        email=email,
        first_name="Test",
        last_name="Testovich",
    )

    f_use_case.execute(request)

    # Check that the event has been created in the EventOutbox
    event = EventOutbox.objects.get(event_context__email=email)

    # Verify that the event type is correctly set to "user has been created"
    assert event.event_type == "user has been created"

