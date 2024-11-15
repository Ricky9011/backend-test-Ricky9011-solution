import pytest
from clickhouse_connect.driver import Client
from django.conf import settings

@pytest.fixture
def clickhouse_client():
    client = Client(
        host=settings.CLICKHOUSE_HOST,
        port=settings.CLICKHOUSE_PORT,
        user=settings.CLICKHOUSE_USER,
        password=settings.CLICKHOUSE_PASSWORD,
        database=settings.CLICKHOUSE_SCHEMA,
    )
    yield client
    client.close()

@pytest.fixture(autouse=True)
def clean_clickhouse(clickhouse_client):
    clickhouse_client.command(f"TRUNCATE TABLE {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}")
    yield
    clickhouse_client.command(f"TRUNCATE TABLE {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}")
