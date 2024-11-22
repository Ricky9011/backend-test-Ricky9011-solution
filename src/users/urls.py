from django.urls import path

from src.users.views import CreateUserView

urlpatterns = [
    path("user/", CreateUserView.as_view(), name="create_user"),
]
