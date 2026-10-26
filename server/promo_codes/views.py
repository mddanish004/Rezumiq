"""Promo code endpoints (user-facing redemption)."""

import json

from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt

from api.common.errors import not_allowed
from api.common.guards import require_auth
from api.common.responses import send_data

from . import service


@require_auth
@csrf_exempt
def redeem(request: HttpRequest):
    if request.method != "POST":
        return not_allowed(["POST"])
    raw = json.loads(request.body or b"null")
    code = (raw or {}).get("code", "")
    sub = service.redeem_code(request.user.id, code)
    return send_data(dict, {"id": sub.id, "plan": sub.plan, "status": sub.status}, status=201)
