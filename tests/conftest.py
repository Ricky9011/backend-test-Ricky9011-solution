from collections.abc import Generator

import clickhouse_connect
import pytest
from clickhouse_connect.driver import Client
from django.conf import settings

pytest_plugins = [
    "tests.fixtures.users.request",
    "tests.fixtures.users.use_case",
    "tests.fixtures.users.users",
]


@pytest.fixture(autouse=True)
def use_django_db(db: str) -> None:
    pass


@pytest.fixture(autouse=True)
def clean_up_event_logs(ch_client: Client) -> Generator[None, None, None]:
    ch_client.query(f"TRUNCATE TABLE {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}")
    yield


@pytest.fixture(scope="module")
def ch_client() -> Client:
    client = clickhouse_connect.get_client(host="clickhouse")
    yield client
    client.close()
