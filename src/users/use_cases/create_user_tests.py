import uuid
from collections.abc import Generator

import pytest
from clickhouse_connect.driver import Client
from django.conf import settings

from outbox.models import Outbox
from users.use_cases import CreateUser, CreateUserRequest, UserCreated

pytestmark = [pytest.mark.django_db]


@pytest.fixture(autouse=True)
def f_clean_up_event_log(f_ch_client: Client) -> Generator:
    f_ch_client.query(f'TRUNCATE TABLE {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}')
    yield


def test_user_created(f_use_case: CreateUser) -> None:
    request = CreateUserRequest(
        email='test@email.com', first_name='Test', last_name='Testovich',
    )

    response = f_use_case.execute(request)

    assert response.result.email == 'test@email.com'
    assert response.error == ''


def test_emails_are_unique(f_use_case: CreateUser) -> None:
    request = CreateUserRequest(
        email='test@email.com', first_name='Test', last_name='Testovich',
    )

    f_use_case.execute(request)
    response = f_use_case.execute(request)

    assert response.result is None
    assert response.error == 'User with this email already exists'

@pytest.mark.transactional_db
def test_event_log_entry_published(
    f_use_case: CreateUser,
) -> None:
    email = f'test_{uuid.uuid4()}@email.com'
    request = CreateUserRequest(
        email=email, first_name='Test', last_name='Testovich',
    )

    f_use_case.execute(request)
    log = Outbox.objects.filter(event_type='user_created').values_list(
        'event_type',
        'environment',
        'event_context',
    )

    assert list(log) == [
        (
            'user_created',
            'Local',
            UserCreated(email=email, first_name='Test', last_name='Testovich').model_dump_json(),
        ),
    ]
