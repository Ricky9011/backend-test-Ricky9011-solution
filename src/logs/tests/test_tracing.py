import pytest
from logs.models import OutboxLog
from logs.services import process_logs
from sentry_sdk import capture_message
from pytest import caplog

@pytest.mark.django_db
def test_process_logs_with_tracing(caplog):    
    OutboxLog.objects.create(
        event_type="test_event",
        event_date_time="2024-01-01T12:00:00",
        environment="test",
        event_context={"key": "value"},
    )    
    process_logs(batch_size=10)    
    assert "Processing logs" in caplog.text
    assert "Successfully processed logs" in caplog.text    
    capture_message("Test Sentry Integration")
