import json
import logging
from collections.abc import Generator
from unittest import mock

import clickhouse_connect
import pytest
from clickhouse_connect.driver import Client
from django.conf import settings

from core.models import EventOutbox
from core.tasks import process_event_outbox
from users.use_cases import CreateUser, CreateUserRequest

pytestmark = [pytest.mark.django_db]


@pytest.fixture()
def f_use_case() -> CreateUser:
    return CreateUser()


@pytest.fixture(autouse=True)
def f_clean_up_event_log(f_ch_client: Client) -> Generator:
    f_ch_client.query(f'TRUNCATE TABLE {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}')
    yield

@pytest.fixture
def f_ch_client() -> Client:
    """Fixture for connecting to the real ClickHouse instance"""
    client = clickhouse_connect.get_client(
        host=settings.CLICKHOUSE_HOST,
        port=settings.CLICKHOUSE_PORT,
        user=settings.CLICKHOUSE_USER,
        password=settings.CLICKHOUSE_PASSWORD,
    )

    # Check if the client can connect successfully (optional)
    try:
        client.ping()
    except Exception as e:
        raise RuntimeError(f"Failed to connect to ClickHouse: {e}") from e

    return client


# Test for the case, when clickhouse is up and event is inserted successfully
def test_process_event_outbox_success(f_ch_client: Client, f_use_case: CreateUser) -> None:
    # Add an event to the outbox
    request = CreateUserRequest(
        email='outbox_success@email.com', first_name='Process', last_name='Outbox',
    )
    f_use_case.execute(request)

    # Run process_event_outbox
    process_event_outbox()

    # Query ClickHouse to check if the event was inserted
    query = f"SELECT * FROM {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}"
    result = f_ch_client.query(query)

    # Ensure the event is in the ClickHouse table
    assert len(result.result_rows) > 0
    assert result.result_rows[0][0] == 'user_created'

    event_data = json.loads(json.loads(result.result_rows[0][3]))

    assert event_data == {
        'email': 'outbox_success@email.com',
        'first_name': 'Process',
        'last_name': 'Outbox',
    }

    # Ensure the event was deleted from EventOutbox after processing
    assert EventOutbox.objects.count() == 0



# Test for the case when ClickHouse is down and event is not inserted
def test_process_event_outbox_network_error(
    f_use_case: CreateUser,
    caplog: pytest.LogCaptureFixture,
) -> None:

    # Add an event to the outbox
    request = CreateUserRequest(
        email='outbox_error@email.com', first_name='Error', last_name='Outbox',
    )
    f_use_case.execute(request)

    # Mock ClickHouse client to raise a simulated connection failure
    with mock.patch('clickhouse_connect.get_client') as mock_client:
        mock_client.side_effect = Exception("Simulated network error")

        # Run process_event_outbox and capture logs
        with caplog.at_level(logging.ERROR):
            process_event_outbox()

    assert "Error inserting events to ClickHouse" in caplog.text

    # Assert that the event was not deleted from EventOutbox
    assert EventOutbox.objects.count() == 1

