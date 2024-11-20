import json

from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from src.users.use_cases import CreateUser, CreateUserRequest


@method_decorator(csrf_exempt, name="dispatch")
class CreateUserView(View):
    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            body = json.loads(request.body)
            payload = CreateUserRequest(**body)
        except json.JSONDecodeError:
            return JsonResponse({"result": None, "error": "Invalid JSON"}, status=400)
        except TypeError:
            return JsonResponse(
                {"result": None, "error": "Invalid payload"},
                status=400,
            )

        resp = CreateUser().execute(payload)
        if resp.error:
            return JsonResponse({"result": None, "error": resp.error}, status=400)

        return JsonResponse({"result": {"email": resp.result.email}, "error": None})
