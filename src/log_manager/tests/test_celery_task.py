import json

from celery.schedules import crontab
from clickhouse_connect.driver import Client
from django.conf import settings

import conftest
from log_manager.models import OutboxEvent
from log_manager.tasks import process_outbox


def test_process_outbox_success(f_ch_client: Client, f_sample_outbox_events) -> None:

    process_outbox()

    unprocessed_events = OutboxEvent.objects.filter(status=OutboxEvent.ProcessedStatus.PENDING)
    assert unprocessed_events.count() == 0

    events = f_ch_client.query(f"SELECT * FROM {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}")

    assert len(events.result_rows) == 1

    assert events.result_rows[0][0] == "user_created"
    assert events.result_rows[0][2] == "test"
    assert events.result_rows[0][4] == 1

    assert json.loads(events.result_rows[0][3]) == {
        "email": conftest.TEST_EMAIL,
        "first_name": conftest.TEST_FIRST_NAME,
        "last_name": conftest.TEST_LAST_NAME,
    }


def test_celery_beat_schedule_includes_process_outbox():
    from core.celery import app as celery_app

    assert "process_outbox" in celery_app.conf.beat_schedule

    scheduled_task = celery_app.conf.beat_schedule["process_outbox"]

    assert scheduled_task["task"] == "log_manager.tasks.process_outbox"

    assert scheduled_task["schedule"] == crontab(minute="*/1")
