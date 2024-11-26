# core/tests/test_event_service.py

import pytest
from django.db import DatabaseError

from core.models import OutboxEvent
from core.services.event_service import EventPublishError, EventService
from core.tasks import process_outbox_events

pytestmark = [pytest.mark.django_db]

def test_publish_event_success() -> None:
    """Test successful event publishing"""
    EventService.publish_event('test_event', {'test': 'data'})

    event = OutboxEvent.objects.first()
    assert event.event_type == 'test_event'
    assert event.event_data == {'test': 'data'}
    assert event.status == OutboxEvent.STATUS_PENDING

def test_publish_event_database_error(mocker: any) -> None:
    """Test handling of database errors during event publishing"""
    mocker.patch('core.models.OutboxEvent.objects.create',
                 side_effect=DatabaseError("Test DB Error"))

    with pytest.raises(EventPublishError) as exc_info:
        EventService.publish_event('test_event', {'test': 'data'})

    assert "Failed to publish event" in str(exc_info.value)

def test_publish_event() -> None:
    """Test that events are correctly saved to outbox"""
    event_data = {'test': 'data'}

    EventService.publish_event('test_event', event_data)

    event = OutboxEvent.objects.first()
    assert event.event_type == 'test_event'
    assert event.event_data == event_data
    assert event.status == OutboxEvent.STATUS_PENDING



def test_process_outbox_events(f_ch_client: any) -> None:
    """Test that events are correctly processed and sent to ClickHouse"""
    # Create test event
    OutboxEvent.objects.create(
        event_type='test_event',
        event_data={'test': 'data'},
    )

    # Run task
    process_outbox_events()

    # Check ClickHouse
    result = f_ch_client.query(
        "SELECT * FROM default.event_log WHERE event_type = 'test_event'",
    )
    assert len(result.result_rows) == 1

    # Check event status
    event = OutboxEvent.objects.first()
    assert event.status == OutboxEvent.STATUS_PROCESSED
    assert event.processed_at is not None
