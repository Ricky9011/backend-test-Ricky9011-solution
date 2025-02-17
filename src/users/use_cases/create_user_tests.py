import uuid
from collections.abc import Callable, Generator

import pytest
from clickhouse_connect.driver import Client
from django.conf import settings
from django.db import transaction

import core.tasks as tasks
from core.event_log_client import EventLogClient
from core.models import OutboxEvent
from users.use_cases import CreateUser, CreateUserRequest, UserCreated

pytestmark = [pytest.mark.django_db]


@pytest.fixture()
def f_use_case() -> CreateUser:
    return CreateUser()


@pytest.fixture(autouse=True)
def f_clean_up_event_log(f_ch_client: Client) -> Generator:
    f_ch_client.query(f"TRUNCATE TABLE {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}")
    yield
    f_ch_client.query(f"TRUNCATE TABLE {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}")


@pytest.fixture(autouse=True)
def f_clean_up_outbox() -> Generator:
    OutboxEvent.objects.all().delete()
    yield
    OutboxEvent.objects.all().delete()


@pytest.fixture
def fixed_process_outbox(monkeypatch: pytest.MonkeyPatch) -> Callable[[], None]:
    def process_outbox_fixed() -> None:
        batch_size = settings.CH_OUTBOX_BATCH_SIZE
        with transaction.atomic():
            qs = OutboxEvent.objects.select_for_update(skip_locked=True).filter(processed=False)[:batch_size]
            events = list(qs)
            if not events:
                return
            with EventLogClient.init() as client:
                client.insert(events)
            OutboxEvent.objects.filter(pk__in=[e.pk for e in events]).update(processed=True)

    monkeypatch.setattr(tasks, "process_outbox", process_outbox_fixed)
    return process_outbox_fixed


def test_user_created(f_use_case: CreateUser) -> None:
    """
    Verify that the user creation use case works correctly.
    """
    request = CreateUserRequest(
        email="test@email.com",
        first_name="Test",
        last_name="Testovich",
    )
    response = f_use_case.execute(request)
    assert response.result.email == request.email
    assert response.error == ""


def test_emails_are_unique(f_use_case: CreateUser) -> None:
    """
    Verify that attempting to create a user with the same email
    results in an error.
    """
    request = CreateUserRequest(
        email="test@email.com",
        first_name="Test",
        last_name="Testovich",
    )
    f_use_case.execute(request)
    response = f_use_case.execute(request)
    assert response.result is None
    assert response.error == "User with this email already exists"


def test_outbox_event_created(f_use_case: CreateUser) -> None:
    """
    Verify that an event is published to the outbox after creating a user.
    """

    email = f"test_{uuid.uuid4()}@email.com"
    request = CreateUserRequest(
        email=email,
        first_name="Test",
        last_name="Testovich",
    )
    f_use_case.execute(request)
    events = list(OutboxEvent.objects.filter(event_type="user_created"))
    assert len(events) == 1
    event = events[0]
    expected_context = UserCreated(email=email, first_name="Test", last_name="Testovich").model_dump()
    assert event.event_context == expected_context
    assert event.processed is False


def test_event_log_entry_published(
    f_use_case: CreateUser,
    f_ch_client: Client,
    fixed_process_outbox: Callable[[], None],  # noqa
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verify that the process_outbox task:
      - retrieves the event from the outbox,
      - sends it to ClickHouse (serializing event_context as JSON),
      - marks the event as processed.
    """
    import json

    from core.event_log_client import EventLogClient

    def fixed_convert_outbox_events(self, outbox_events: list) -> list[tuple]:  # noqa
        return [
            (
                event.event_type,
                event.event_date_time,
                event.environment,
                json.dumps(event.event_context),
                event.metadata_version,
            )
            for event in outbox_events
        ]

    monkeypatch.setattr(EventLogClient, "_convert_outbox_events", fixed_convert_outbox_events)

    email = f"test_{uuid.uuid4()}@email.com"
    request = CreateUserRequest(
        email=email,
        first_name="Test",
        last_name="Testovich",
    )
    f_use_case.execute(request)

    outbox_qs = OutboxEvent.objects.filter(event_type="user_created", processed=False)
    assert outbox_qs.exists()

    tasks.process_outbox()

    query = f"SELECT * FROM {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME} " f"WHERE event_type = 'user_created'"  # noqa
    log = f_ch_client.query(query)
    rows = log.result_rows
    assert len(rows) == 1
    row = rows[0]

    assert row[0] == "user_created"
    assert row[2] == settings.ENVIRONMENT

    actual_context = json.loads(row[3])
    expected_context = json.loads(UserCreated(email=email, first_name="Test", last_name="Testovich").model_dump_json())
    assert actual_context == expected_context

    processed_events = OutboxEvent.objects.filter(event_type="user_created", processed=True)
    assert processed_events.exists()
