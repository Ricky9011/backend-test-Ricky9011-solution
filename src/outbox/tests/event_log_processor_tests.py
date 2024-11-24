import uuid

import pytest
from clickhouse_connect.driver import Client
from django.conf import settings

from outbox.models import EventLogOutbox
from users.use_cases import CreateUser, CreateUserRequest, UserCreated

pytestmark = pytest.mark.django_db


@pytest.fixture
def use_case() -> CreateUser:
    return CreateUser()


@pytest.fixture
def clean_event_log(ch_client: Client):
    ch_client.query(f"TRUNCATE TABLE {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}")
    yield
    ch_client.query(f"TRUNCATE TABLE {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}")


def test_outbox_entry_created(use_case):
    request = CreateUserRequest(
        email=f"test_{uuid.uuid4()}@email.com", first_name="Test", last_name="Testovich"
    )

    use_case.execute(request)

    event = EventLogOutbox.objects.filter(event_type="user_created").first()

    assert event is not None
    assert event.payload["email"] == request.email
    assert event.payload["first_name"] == request.first_name
    assert event.payload["last_name"] == request.last_name


def test_outbox_entry_processed(ch_client, use_case, clean_event_log):
    """Проверка, что событие обрабатывается из Outbox и отправляется в ClickHouse."""
    email = f"test_{uuid.uuid4()}@email.com"
    request = CreateUserRequest(
        email=email, first_name="Test", last_name="Testovich"
    )

    use_case.execute(request)

    log = ch_client.query(
        f"SELECT * FROM {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME} WHERE event_type = 'user_created'"
    )

    assert len(log.result_rows) == 1
    event = log.result_rows[0]

    assert event[0] == "user_created"
    assert event[2] == "Local"
    assert event[3] == UserCreated(email=email, first_name="Test", last_name="Testovich").model_dump_json()
    assert event[4] == 1


def test_outbox_entry_not_processed_on_failure(use_case, mocker):
    mocker.patch(
        "outbox.processors.EventLogProcessor.process_events",
        side_effect=Exception("Processing error"),
    )
    request = CreateUserRequest(
        email=f"test_{uuid.uuid4()}@email.com", first_name="Test", last_name="Testovich"
    )

    use_case.execute(request)

    event = EventLogOutbox.objects.filter(event_type="user_created").first()
    assert event is not None
    assert event.processed_at is None
