import pytest

from src.users.use_cases import CreateUserRequest


@pytest.fixture
def create_user_request() -> CreateUserRequest:
    return CreateUserRequest(
        email="test@email.com",
        first_name="Test",
        last_name="Testovich",
    )
