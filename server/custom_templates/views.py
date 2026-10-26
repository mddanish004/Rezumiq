"""Custom template endpoints, ported from modules/custom-templates."""

import json

from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from api.common.errors import AppError, not_allowed
from api.common.guards import require_auth
from api.common.parse import parse_body
from api.common.responses import send_data

from . import service
from .schemas import (
    CustomTemplateDetail,
    CustomTemplateSummary,
    UpdateCustomTemplateBody,
)


@require_auth
@csrf_exempt
def custom_templates(request: HttpRequest):
    if request.method == "GET":
        rows = service.list_custom_templates(request.user.id)
        return send_data(list[CustomTemplateSummary], rows)
    if request.method == "POST":
        raw = json.loads(request.body or b"null")
        if not isinstance(raw, dict) or "type" not in raw or "name" not in raw:
            raise AppError(400, "VALIDATION_ERROR", "Request validation failed")
        if raw["type"] == "tex":
            if "texSource" not in raw:
                raise AppError(400, "VALIDATION_ERROR", "Request validation failed")
        else:
            if "resumeId" not in raw:
                raise AppError(400, "VALIDATION_ERROR", "Request validation failed")
        data = service.create_custom_template(request.user.id, raw)
        return send_data(CustomTemplateDetail, data, status=201)
    return not_allowed(["GET", "POST"])


@require_auth
@csrf_exempt
def custom_template_detail(request: HttpRequest, custom_template_id):
    if request.method == "GET":
        data = service.get_custom_template(request.user.id, custom_template_id)
        return send_data(CustomTemplateDetail, data)
    if request.method == "PATCH":
        body = parse_body(UpdateCustomTemplateBody, request)
        changes = body.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = service.update_custom_template(request.user.id, custom_template_id, changes)
        return send_data(CustomTemplateDetail, data)
    if request.method == "DELETE":
        service.delete_custom_template(request.user.id, custom_template_id)
        return HttpResponse(status=204)
    return not_allowed(["GET", "PATCH", "DELETE"])
