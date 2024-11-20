import json
import uuid
from unittest.mock import ANY

import pytest
from clickhouse_connect.driver import Client

from src.logs.models import OutboxLog
from src.users.models import User
from src.users.use_cases import CreateUser, CreateUserRequest, UserCreated


class TestUserCreated:
    def test_user_created(
        self,
        create_user_uc: CreateUser,
        create_user_request: CreateUserRequest,
    ) -> None:
        assert User.objects.count() == 0
        assert OutboxLog.objects.count() == 0

        resp = create_user_uc.execute(create_user_request)
        assert resp.result is not None
        assert resp.error == ""

        assert User.objects.count() == 1
        user = User.objects.get()
        assert user.email == create_user_request.email
        assert user.first_name == create_user_request.first_name
        assert user.last_name == create_user_request.last_name

        assert resp.result.email == user.email
        assert resp.result.first_name == user.first_name
        assert resp.result.last_name == user.last_name

        assert OutboxLog.objects.count() == 1
        log = OutboxLog.objects.get()
        assert log.event_type == "user_created"
        assert json.loads(log.event_context) == {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
        assert log.exported_at is None

    def test_email_is_unique(
        self,
        user_test_testovich: User,
        create_user_uc: CreateUser,
        create_user_request: CreateUserRequest,
    ) -> None:
        assert User.objects.count() == 1
        assert OutboxLog.objects.count() == 0

        resp = create_user_uc.execute(create_user_request)
        assert resp.result is None
        assert resp.error == "User with this email already exists"

        assert User.objects.count() == 1
        assert User.objects.get() == user_test_testovich

        assert OutboxLog.objects.count() == 0


@pytest.mark.skip
def test_event_log_entry_published(
    create_user_uc: CreateUser,
    ch_client: Client,
) -> None:
    email = f"test_{uuid.uuid4()}@email.com"
    request = CreateUserRequest(
        email=email,
        first_name="Test",
        last_name="Testovich",
    )

    create_user_uc.execute(request)
    log = ch_client.query(
        "SELECT * FROM default.event_log WHERE event_type = 'user_created'",
    )

    assert log.result_rows == [
        (
            "user_created",
            ANY,
            "Local",
            UserCreated(
                email=email,
                first_name="Test",
                last_name="Testovich",
            ).model_dump_json(),
            1,
        ),
    ]
