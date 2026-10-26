"""Analytics endpoints."""

from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt

from api.common.errors import not_allowed
from api.common.guards import require_auth
from api.common.parse import parse_query
from api.common.responses import send_data

from . import service
from .schemas import AnalyticsQuery, AnalyticsResponse


@require_auth
@csrf_exempt
def analytics(request: HttpRequest):
    if request.method != "GET":
        return not_allowed(["GET"])
    query = parse_query(AnalyticsQuery, request)
    data = service.get_analytics(request.user.id, query.days, query.time_zone)
    return send_data(AnalyticsResponse, data)


@require_auth
@csrf_exempt
def analytics_insights(request: HttpRequest):
    if request.method != "GET":
        return not_allowed(["GET"])
    from usage.quotas import assert_paid_plan

    assert_paid_plan(request.user.id, "Detailed analytics")
    query = parse_query(AnalyticsQuery, request)
    data = service.get_insights(request.user.id, query.days, query.time_zone)
    return send_data(dict, data)


@require_auth
@csrf_exempt
def analytics_views(request: HttpRequest):
    if request.method != "GET":
        return not_allowed(["GET"])
    from usage.quotas import assert_paid_plan

    assert_paid_plan(request.user.id, "Exporting views")
    query = parse_query(AnalyticsQuery, request)
    data = service.export_views(request.user.id, query.days)
    return send_data(list, data)
