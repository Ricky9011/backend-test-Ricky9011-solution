import pytest
from users.models import User
from users.use_cases.create_user import CreateUser, CreateUserRequest

@pytest.mark.django_db
def test_create_user():
    request = CreateUserRequest(
        email="test@example.com", first_name="Test", last_name="User"
    )
    use_case = CreateUser()
    response = use_case.execute(request)    
    assert response.error == ""
    assert response.result.email == "test@example.com"
    assert User.objects.count() == 1
