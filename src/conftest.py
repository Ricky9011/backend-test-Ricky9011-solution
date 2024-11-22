from collections.abc import Generator

import clickhouse_connect
import pytest
from clickhouse_connect.driver import Client
from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper

from users.use_cases import CreateUser


@pytest.fixture(scope='module')
def f_ch_client() -> Client:
    client = clickhouse_connect.get_client(host='clickhouse')
    yield client
    client.close()


@pytest.fixture(scope='function')
@pytest.mark.transactional_db
def f_pg_client()-> Generator[BaseDatabaseWrapper, None, None]:
    conn = connections['default']
    yield conn
    conn.close()


@pytest.fixture()
def f_use_case() -> CreateUser:
    return CreateUser()

