# src/core/tests/test_observability.py

from unittest.mock import patch

import pytest

from core.observability import trace_event


def test_trace_event_decorator() -> None:
    """Test that trace_event decorator properly handles success and failure cases"""

    # Test successful case
    @trace_event("test_operation")
    def successful_function() -> str:
        return "success"

    with patch("sentry_sdk.start_transaction") as mock_transaction:
        result = successful_function()
        assert result == "success"
        mock_transaction.assert_called_once()

    # Test error case
    @trace_event("test_operation")
    def failing_function() -> None:
        raise ValueError("test error")

    with patch("sentry_sdk.start_transaction") as mock_transaction:
        with pytest.raises(ValueError):
            failing_function()
        mock_transaction.assert_called_once()
