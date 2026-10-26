"""Admin endpoints, ported from admin.routes.ts.

Every route sits behind require_auth + require_admin (see api/common/guards.py).
"""

from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from api.common.errors import not_allowed
from api.common.guards import require_admin
from api.common.parse import parse_body, parse_query, validate
from api.common.responses import send_data

from . import service
from .schemas import (
    AdminAiOut,
    AdminContentOut,
    AdminContentQuery,
    AdminOverviewOut,
    AdminRangeQuery,
    AdminRevenueOut,
    AdminSubscriptionParams,
    AdminSystemOut,
    AdminTrafficOut,
    AdminUserListOut,
    AdminUserOut,
    AdminUserParams,
    AdminUsersQuery,
    CreateAdminSubscriptionBody,
    UpdateAdminUserBody,
)


def _user_id(raw) -> int:
    return validate(AdminUserParams, {"user_id": raw}, "params").user_id


def _subscription_id(raw) -> str:
    return str(
        validate(AdminSubscriptionParams, {"subscription_id": raw}, "params").subscription_id
    )


@require_admin
@csrf_exempt
def overview(request: HttpRequest):
    if request.method != "GET":
        return not_allowed(["GET"])
    query = parse_query(AdminRangeQuery, request)
    return send_data(AdminOverviewOut, service.get_overview(query.days, query.time_zone))


@require_admin
@csrf_exempt
def users(request: HttpRequest):
    if request.method != "GET":
        return not_allowed(["GET"])
    query = parse_query(AdminUsersQuery, request)
    return send_data(AdminUserListOut, service.list_users(query.model_dump()))


@require_admin
@csrf_exempt
def user_detail(request: HttpRequest, user_id):
    if request.method not in ("GET", "PATCH"):
        return not_allowed(["GET", "PATCH"])
    user_id = _user_id(user_id)
    if request.method == "GET":
        return send_data(AdminUserOut, service.get_user_detail(user_id))
    body = parse_body(UpdateAdminUserBody, request)
    service.set_suspended(request.user.id, user_id, body.suspended)
    return send_data(AdminUserOut, service.get_user_detail(user_id))


@require_admin
@csrf_exempt
def revoke_sessions(request: HttpRequest, user_id):
    if request.method != "DELETE":
        return not_allowed(["DELETE"])
    service.revoke_sessions(request.user.id, _user_id(user_id))
    return HttpResponse(status=204)


@require_admin
@csrf_exempt
def reset_usage(request: HttpRequest, user_id):
    if request.method != "DELETE":
        return not_allowed(["DELETE"])
    service.reset_usage(request.user.id, _user_id(user_id))
    return HttpResponse(status=204)


@require_admin
@csrf_exempt
def grant_subscription(request: HttpRequest, user_id):
    if request.method != "POST":
        return not_allowed(["POST"])
    user_id = _user_id(user_id)
    body = parse_body(CreateAdminSubscriptionBody, request)
    service.grant_subscription(request.user.id, user_id, body.plan, body.months)
    return send_data(AdminUserOut, service.get_user_detail(user_id), status=201)


@require_admin
@csrf_exempt
def revoke_subscription(request: HttpRequest, user_id, subscription_id):
    if request.method != "DELETE":
        return not_allowed(["DELETE"])
    service.revoke_subscription(
        request.user.id, _user_id(user_id), _subscription_id(subscription_id)
    )
    return HttpResponse(status=204)


@require_admin
@csrf_exempt
def ai_usage(request: HttpRequest):
    if request.method != "GET":
        return not_allowed(["GET"])
    query = parse_query(AdminRangeQuery, request)
    return send_data(AdminAiOut, service.get_ai_usage(query.days, query.time_zone))


@require_admin
@csrf_exempt
def revenue(request: HttpRequest):
    if request.method != "GET":
        return not_allowed(["GET"])
    query = parse_query(AdminRangeQuery, request)
    return send_data(AdminRevenueOut, service.get_revenue(query.days, query.time_zone))


@require_admin
@csrf_exempt
def content(request: HttpRequest):
    if request.method != "GET":
        return not_allowed(["GET"])
    query = parse_query(AdminContentQuery, request)
    return send_data(AdminContentOut, service.get_content(query.days))


@require_admin
@csrf_exempt
def traffic(request: HttpRequest):
    if request.method != "GET":
        return not_allowed(["GET"])
    query = parse_query(AdminRangeQuery, request)
    return send_data(AdminTrafficOut, service.get_traffic(query.days, query.time_zone))


@require_admin
@csrf_exempt
def system(request: HttpRequest):
    if request.method != "GET":
        return not_allowed(["GET"])
    return send_data(AdminSystemOut, service.get_system())
