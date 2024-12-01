import uuid
from unittest.mock import ANY, patch

import pytest

from log_manager.models import OutboxEvent
from users.models import User
from users.use_cases import CreateUser, CreateUserRequest, UserCreated

pytestmark = [pytest.mark.django_db]


@pytest.fixture()
def f_use_case() -> CreateUser:
    return CreateUser()


def test_user_created(f_use_case: CreateUser) -> None:
    request = CreateUserRequest(
        email="test@email.com",
        first_name="Test",
        last_name="Testovich",
    )

    response = f_use_case.execute(request)

    assert response.result.email == "test@email.com"
    assert response.error == ""


def test_emails_are_unique(f_use_case: CreateUser) -> None:
    request = CreateUserRequest(
        email="test@email.com",
        first_name="Test",
        last_name="Testovich",
    )

    f_use_case.execute(request)
    response = f_use_case.execute(request)

    assert response.result is None
    assert response.error == "User with this email already exists"


def test_event_log_entry_published(
    f_use_case: CreateUser,
) -> None:
    email = f"test_{uuid.uuid4()}@email.com"
    request = CreateUserRequest(
        email=email,
        first_name="Test",
        last_name="Testovich",
    )

    f_use_case.execute(request)
    log = OutboxEvent.objects.filter(event_type="user_created")
    assert log.count() == 1
    log = log.first()

    assert log.event_type == "user_created"
    assert log.environment == "Local"
    assert log.event_context == UserCreated(email=email, first_name="Test", last_name="Testovich").model_dump_json()
    assert log.metadata_version == 1
    assert log.created_at == ANY


def test_user_creation_rolled_back_on_event_log_failure(f_use_case: CreateUser) -> None:
    """
    The test checks that if an event logging error occurs, the user is not created.
    """
    with patch("core.event_log_client.EventLogClient.insert") as mock_log_event:
        mock_log_event.side_effect = Exception("Failed to log event")

        request = CreateUserRequest(
            email="test_rollback@example.com",
            first_name="Rollback",
            last_name="Tester",
        )
        with pytest.raises(Exception) as exc_info:
            f_use_case.execute(request)

        assert "Failed to log event" in str(exc_info.value)

        users_count = User.objects.count()
        assert users_count == 0
