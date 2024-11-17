import clickhouse_connect
import pytest
from clickhouse_connect.driver import Client
from redis import Redis


@pytest.fixture(scope='module')
def f_ch_client() -> Client:
    client = clickhouse_connect.get_client(host='clickhouse')
    yield client
    client.close()


@pytest.fixture(scope='module')
def f_redis_client() -> Client:
    client = Redis(host='redis', port=6379, decode_responses=True)
    yield client
    client.close()
