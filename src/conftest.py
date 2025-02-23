from datetime import timezone

import clickhouse_connect
import pytest
from clickhouse_connect.driver import Client

from src.logs.models import EventLogOutbox


@pytest.fixture(scope='module')
def f_ch_client() -> Client:
    client = clickhouse_connect.get_client(host='clickhouse')
    yield client
    client.close()

@pytest.mark.djando_db
def test_event_log_outbox_creation(test_event_data):
    event = EventLogOutbox.objects.create(
        event_type=test_event_data["type"],
        event_date_time=test_event_data["timestamp"],
        environment=test_event_data["env"],
        event_context=test_event_data["context"],
        metadata_version=test_event_data["version"]
    )

    assert event.processed is False
    assert str(event.id) != ""
    assert event.created_at <= timezone.now()


@pytest.mark.django_db
def test_outbox_processing(settings):
    settings.CLICKHOUSE_DB = 'test_db'

    # Create test event
    EventLogOutbox.objects.create(
        event_type='test',
        event_date_time=timezone.now(),
        environment='test',
        event_context={'key': 'value'},
        metadata_version=1,
    )

    # Process batch
    from logs.task import process_outbox_batch
    process_outbox_batch.delay().get()

    # Verify ClickHouse
    client = Client(host=settings.CLICKHOUSE_HOST, port=settings.CLICKHOUSE_PORT)
    result = client.execute("SELECT count() FROM event_logs")
    assert result[0][0] == 1