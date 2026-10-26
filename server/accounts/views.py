import secrets
import shutil
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from api.common.errors import not_allowed
from api.common.guards import require_auth
from api.common.parse import parse_body
from api.common.responses import send_data

from .schemas import MeOut, UpdateMeBody, UsernameOut
from .service import delete_me, export_my_data, update_me, with_admin
from .usernames import is_username_available


def health(request) -> JsonResponse:
    return JsonResponse({"status": "ok"})


def health_deep(request) -> JsonResponse:
    """Component check for the uptime job: Postgres answers and Tectonic is installed."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        database = "ok"
    except Exception:  # noqa: BLE001
        database = "error"

    compiler = "ok" if shutil.which(settings.TECTONIC_BIN) else "missing"

    components = {"database": database, "compiler": compiler}
    healthy = all(value == "ok" for value in components.values())
    return JsonResponse(
        {"status": "ok" if healthy else "unhealthy", "components": components},
        status=200 if healthy else 503,
    )


@require_POST
@csrf_exempt
def guest_login(request) -> JsonResponse:
    """Sign in as a fresh guest account. Dev-only: prod keeps it switched off."""
    if not settings.ENABLE_GUEST_LOGIN:
        return JsonResponse({"detail": "Guest login is not available"}, status=403)

    token = secrets.token_hex(8)
    User = get_user_model()
    user = User.objects.create_user(
        username=f"guest_{token}",
        email=f"{token}@guest.invalid",
        password=None,
        is_guest=True,
        guest_expires_at=timezone.now() + timedelta(days=settings.GUEST_TTL_DAYS),
    )
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return JsonResponse(
        {"ok": True, "user": {"id": user.pk, "username": user.username}}, status=201
    )


@require_auth
@csrf_exempt
def me(request) -> HttpResponse:
    """GET returns the account, PATCH renames it, DELETE closes it."""
    user = request.user

    if request.method == "GET":
        return send_data(MeOut, with_admin(user))
    if request.method == "PATCH":
        body = parse_body(UpdateMeBody, request)
        update_me(user, name=body.name, username=body.username)
        return send_data(MeOut, with_admin(user))
    if request.method == "DELETE":
        delete_me(user)
        return HttpResponse(status=204)
    return not_allowed(["GET", "PATCH", "DELETE"])


@require_auth
def my_data(request) -> JsonResponse:
    """Everything stored about the account, for data portability requests."""
    response = JsonResponse({"data": export_my_data(user=request.user)})
    response["Content-Disposition"] = 'attachment; filename="my-data.json"'
    return response


def username_availability(request, username: str) -> JsonResponse:
    """Checks whether a username is free, for the rename form."""
    username = username.strip().lower()
    return send_data(
        UsernameOut, {"username": username, "available": is_username_available(username)}
    )
