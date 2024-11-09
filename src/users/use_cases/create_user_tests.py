import logging
import uuid
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from clickhouse_connect.driver import Client
from django.conf import settings

from core.models import EventOutbox
from core.tasks import process_event_outbox
from users.use_cases import CreateUser, CreateUserRequest, UserCreated

pytestmark = [pytest.mark.django_db]


@pytest.fixture()
def f_use_case() -> CreateUser:
    return CreateUser()


@pytest.fixture(autouse=True)
def f_clean_up_event_log(f_ch_client: Client) -> Generator:
    f_ch_client.query(f'TRUNCATE TABLE {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}')
    yield


@pytest.fixture
def mock_clickhouse_client(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_client = MagicMock()
    monkeypatch.setattr("clickhouse_connect.get_client", lambda: mock_client)
    return mock_client


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


# Test for the case, when clickhouse is up and event is inserted successfully
def test_process_event_outbox_success(mock_clickhouse_client: MagicMock, f_use_case: CreateUser) -> None:
    # Add an event to the outbox
    request = CreateUserRequest(
        email='outbox_success@email.com', first_name='Process', last_name='Outbox',
    )
    f_use_case.execute(request)

    # Run process_event_outbox
    process_event_outbox()

    # Check that insert method of the mock clickhouse client was called only once, no duplicate events
    mock_clickhouse_client.insert.assert_called_once()

    # Ensure the event was deleted from EventOutbox after processing
    assert EventOutbox.objects.count() == 0


# Test for the case, when clickhouse is down and event is not inserted
def test_process_event_outbox_network_error(
    mock_clickhouse_client: MagicMock,
    f_use_case: CreateUser,
    caplog: pytest.LogCaptureFixture,
) -> None:

    # Simulate a clickhouse connection failure
    mock_clickhouse_client.insert.side_effect = Exception("Network error")

    # Add an event to the outbox
    request = CreateUserRequest(
        email='outbox_error@email.com', first_name='Error', last_name='Outbox',
    )
    f_use_case.execute(request)

    # Run process_event_outbox and capture logs
    with caplog.at_level(logging.ERROR):
        process_event_outbox()


    # Assert that error was logged
    assert any("Error inserting events to ClickHouse" in record.message for record in caplog.records), (
        "Expected error log not found in captured logs"
    )

    # Assert that the event was not deleted from EventOutbox
    assert EventOutbox.objects.count() == 1
