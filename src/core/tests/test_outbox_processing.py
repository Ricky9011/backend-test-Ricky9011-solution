# src/core/tests/test_outbox_processing.py

from unittest.mock import Mock, patch

import pytest

from core.models import OutboxEvent
from core.tasks import process_outbox_events

pytestmark = [pytest.mark.django_db]

class MockContextManager:
    """Helper class to mock context managers"""
    def __init__(self, mock_return: any) -> None:
        self.mock_return = mock_return

    def __enter__(self) -> any:
        return self.mock_return

    def __exit__(self, *args: any) -> None:
        pass

def test_process_outbox_events_sentry_integration() -> None:
    """
    Test that Sentry transaction is properly created and populated
    during event processing
    """
    # Create test event
    test_event = OutboxEvent.objects.create(
        event_type='test_event',
        event_data={'test': 'data'},
    )

    # Create mock for ClickHouse client
    mock_ch_client = Mock()
    mock_ch_client.insert = Mock()

    # Create mock for Sentry transaction
    mock_transaction = Mock()
    mock_transaction.set_data = Mock()
    mock_transaction.set_status = Mock()

    with patch('core.tasks.start_transaction', return_value=MockContextManager(mock_transaction)) as mock_start_trans, \
         patch('core.event_log_client.EventLogClient.init', return_value=MockContextManager(mock_ch_client)):

        # Run the task
        process_outbox_events()

        # Verify transaction was started
        mock_start_trans.assert_called_once_with(
            op="process_events",
            name="process_outbox_events",
        )

        # Verify event was processed
        test_event.refresh_from_db()
        assert test_event.status == OutboxEvent.STATUS_PROCESSED

def test_process_outbox_events_sentry_error_handling() -> None:
    """
    Test that Sentry transaction properly handles and records errors
    """
    # Create test event
    test_event = OutboxEvent.objects.create(
        event_type='test_event',
        event_data={'test': 'data'},
    )

    # Create mock for Sentry transaction
    mock_transaction = Mock()
    mock_transaction.set_data = Mock()
    mock_transaction.set_status = Mock()

    class FailingContextManager:
        def __enter__(self) -> any:
            raise Exception("Test error")
        def __exit__(self, *args: any) -> None:
            pass

    with patch('core.tasks.start_transaction', return_value=MockContextManager(mock_transaction)) as mock_start_trans, \
         patch('core.event_log_client.EventLogClient.init', return_value=FailingContextManager()):

        # Run the task
        process_outbox_events()

        # Verify transaction was used
        mock_start_trans.assert_called_once()
        mock_transaction.set_status.assert_called_with("internal_error")

        # Verify event was marked as failed
        test_event.refresh_from_db()
        assert test_event.status == OutboxEvent.STATUS_FAILED
        assert "Test error" in test_event.error_message
        assert test_event.retry_count == 1
