import pytest
from logs.models import OutboxLog
from logs.services import process_logs
from clickhouse_connect.driver import Client
from django.conf import settings

@pytest.mark.django_db
def test_process_logs_inserts_into_clickhouse(clickhouse_client):    
    OutboxLog.objects.create(
        event_type="test_event",
        event_date_time="2024-01-01T12:00:00",
        environment="test",
        event_context={"key": "value"},
    )
    
    process_logs(batch_size=10)
    
    result = clickhouse_client.query(
        f"SELECT * FROM {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME} WHERE event_type = 'test_event'"
    )
    assert len(result.result_rows) == 1
    assert result.result_rows[0] == (
        "test_event",
        "2024-01-01 12:00:00",
        "test",
        '{"key": "value"}',
        1,
    )
