import pytest
from src.core.models import EventLogOutbox
from src.core.services import EventLogService
from clickhouse_connect import get_client
from django.conf import settings
from django.utils import timezone

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def ch_client():
    client = get_client(
        host=settings.CLICKHOUSE_HOST,
        port=settings.CLICKHOUSE_PORT,
        username=settings.CLICKHOUSE_USER,
        password=settings.CLICKHOUSE_PASSWORD,
    )
    yield client
    client.close()


def test_send_unprocessed_logs(ch_client):
    EventLogOutbox.objects.create(
        event_type='test_event',
        event_date_time=timezone.now(),
        environment='Test',
        event_context={'key': 'value'},
        metadata_version=1,
        processed=False,
    )

    service = EventLogService()
    service.send_unprocessed_logs()

    result = ch_client.query(
        f"SELECT * FROM {settings.CLICKHOUSE_SCHEMA}.{settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME} WHERE event_type = 'test_event'"
    )
    assert len(result.result_rows) == 1

    assert EventLogOutbox.objects.filter(processed=False).count() == 0
