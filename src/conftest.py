import clickhouse_connect
import pytest
from clickhouse_connect.driver import Client
from django.conf import settings


@pytest.fixture(scope='module')
def f_ch_client() -> Client:
    client = clickhouse_connect.get_client(host=settings.CLICKHOUSE_HOST)
    yield client
    client.close()
