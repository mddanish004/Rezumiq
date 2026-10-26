"""Suggestion endpoints."""

from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt

from api.common.errors import not_allowed
from api.common.guards import require_auth
from api.common.parse import parse_body
from api.common.responses import send_data

from . import service
from .schemas import (
    ApplySuggestionBody,
    ApplySuggestionOut,
    CreateSuggestionBody,
    SuggestionResponse,
)


@require_auth
@csrf_exempt
def suggestions(request: HttpRequest, resume_id):
    if request.method == "GET":
        return send_data(
            list[SuggestionResponse], service.list_suggestions(request.user.id, resume_id)
        )
    if request.method == "POST":
        body = parse_body(CreateSuggestionBody, request)
        raw = body.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = service.create_suggestion(request.user.id, resume_id, raw)
        return send_data(SuggestionResponse, data, status=201)
    return not_allowed(["GET", "POST"])


@require_auth
@csrf_exempt
def suggestion_detail(request: HttpRequest, resume_id, suggestion_id):
    if request.method == "GET":
        return send_data(
            SuggestionResponse, service.get_suggestion(request.user.id, resume_id, suggestion_id)
        )
    return not_allowed(["GET"])


@require_auth
@csrf_exempt
def apply_suggestion(request: HttpRequest, resume_id, suggestion_id):
    if request.method != "POST":
        return not_allowed(["POST"])
    body = parse_body(ApplySuggestionBody, request)
    result = service.apply_suggestion(
        request.user.id, resume_id, suggestion_id, body.accepted_operation_ids
    )
    return send_data(ApplySuggestionOut, result)
