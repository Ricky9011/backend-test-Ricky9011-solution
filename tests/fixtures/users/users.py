import pytest

from src.users.models import User


@pytest.fixture
def user_test_testovich() -> User:
    return User.objects.create(
        email="test@email.com",
        first_name="Test",
        last_name="Testovich",
    )
