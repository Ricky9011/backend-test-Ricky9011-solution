from datetime import timedelta

import pytest

from src.logs.models import OutboxLog
from tests.constants import DEFAULT_DATETIME


@pytest.fixture
def daily_outbox_logs() -> list[OutboxLog]:
    objs = OutboxLog.objects.bulk_create(
        [
            OutboxLog(
                event_type="test",
                event_date_time=DEFAULT_DATETIME + timedelta(days=day),
                environment="dev",
                event_context="{}",
                metadata_version=1,
                exported_at=DEFAULT_DATETIME + timedelta(days=day) if day < 6 else None,
            )
            for day in range(10)
        ],
    )
    return objs
