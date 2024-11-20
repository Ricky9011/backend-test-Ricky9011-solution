import pytest

from src.users.use_cases import CreateUser


@pytest.fixture
def create_user_uc() -> CreateUser:
    return CreateUser()
