import pytest
from logs.models import OutboxLog
from logs.tasks import process_outbox_task
from clickhouse_connect.driver import Client
from django.conf import settings

@pytest.mark.django_db
def test_process_outbox_task(clickhouse_client):
    OutboxLog.objects.create(
        event_type="test_event",
        event_date_time="2024-01-01T12:00:00",
        environment="test",
        event_context={"key": "value"},
    )
    process_outbox_task()

    result = clickhouse_client.query(
        f"SELECT * FROM {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME} WHERE event_type = 'test_event'"
    )
    assert len(result.result_rows) == 1
