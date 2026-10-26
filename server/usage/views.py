"""Usage endpoint, ported from usage.routes.ts."""

from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt

from api.common.errors import not_allowed
from api.common.guards import require_auth
from api.common.responses import send_data

from .quotas import get_usage
from .schemas import UsageOut


@require_auth
@csrf_exempt
def usage(request: HttpRequest):
    """GET /v1/usage - this period's counters against the plan limits."""
    if request.method != "GET":
        return not_allowed(["GET"])
    return send_data(UsageOut, get_usage(request.user.id))
