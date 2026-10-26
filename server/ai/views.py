"""AI run history endpoint, ported from ai-runs.routes.ts."""

from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt

from api.common.errors import not_allowed
from api.common.guards import require_auth
from api.common.responses import send_data

from .schemas import AiRunListOut
from .service import list_ai_runs


@require_auth
@csrf_exempt
def ai_runs(request: HttpRequest):
    """GET /v1/me/ai-runs"""
    if request.method != "GET":
        return not_allowed(["GET"])
    return send_data(AiRunListOut, list_ai_runs(request.user.id))
