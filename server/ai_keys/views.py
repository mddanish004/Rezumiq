"""AI key endpoints."""

import json

from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from api.common.errors import not_allowed
from api.common.guards import require_auth
from api.common.parse import parse_body
from api.common.responses import send_data

from . import service
from .schemas import AiKeyResponse, UpdateAiKeyBody


@require_auth
@csrf_exempt
def ai_keys(request: HttpRequest):
    if request.method == "GET":
        return send_data(list, service.list_keys(request.user.id))
    return not_allowed(["GET"])


@require_auth
@csrf_exempt
def ai_key_models(request: HttpRequest, provider):
    if request.method != "GET":
        return not_allowed(["GET"])
    return send_data(list, service.list_models(request.user.id, provider))


@require_auth
@csrf_exempt
def ai_key_detail(request: HttpRequest, provider):
    if request.method == "PUT":
        raw = json.loads(request.body or b"null")
        api_key = (raw or {}).get("apiKey") or (raw or {}).get("api_key")
        model_id = (raw or {}).get("modelId") or (raw or {}).get("model_id")
        data = service.put_key(request.user.id, provider, api_key, model_id)
        return send_data(AiKeyResponse, data)
    if request.method == "PATCH":
        body = parse_body(UpdateAiKeyBody, request)
        changes = body.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = service.update_key(
            request.user.id, provider, changes.get("enabled"), changes.get("modelId")
        )
        return send_data(AiKeyResponse, data)
    if request.method == "DELETE":
        service.delete_key(request.user.id, provider)
        return HttpResponse(status=204)
    return not_allowed(["PUT", "PATCH", "DELETE"])
