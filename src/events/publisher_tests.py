from collections.abc import Generator

import pytest
import structlog
from clickhouse_connect.driver import Client
from django.conf import settings

from events.models import EventOutbox
from events.publisher import EventPublisher

logger = structlog.get_logger(__name__)

pytestmark = [pytest.mark.django_db]


@pytest.fixture()
def event_publisher():
    return EventPublisher


@pytest.fixture()
def outboxed_event(db) -> Generator[EventOutbox]:
    event = EventOutbox.objects.create(
        event_type='TestType',
        environment='Test',
        event_context='{Very: Test, Context: Like, Its: Json}',
    )
    yield event
    event.delete()


@pytest.fixture(autouse=True)
def f_clean_up_event_log(f_ch_client: Client) -> Generator:
    f_ch_client.query(f'TRUNCATE TABLE {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}')
    yield


def test_event_log_entry_published(
    outboxed_event: EventOutbox,
    event_publisher: EventPublisher,
    f_ch_client: Client,
) -> None:
    event_publisher.publish()
    log = f_ch_client.query("SELECT * FROM default.event_log WHERE event_type = 'TestType'")

    assert len(log.result_rows) == 1
