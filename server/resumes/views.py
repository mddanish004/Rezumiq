"""The master profile endpoints, ported from modules/profiles."""

from datetime import datetime
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from api.common.errors import AppError, not_allowed
from api.common.guards import require_auth
from api.common.models import ApiModel
from api.common.parse import parse_body, parse_query
from api.common.responses import send_data

from . import service
from .content import EMPTY_RESUME_CONTENT, ResumeContent
from .models import Profile, Template
from .schemas import (
    CreateResumeBody,
    CreateVersionBody,
    ListResumesQuery,
    ListVersionsQuery,
    ResumeDetail,
    ResumeSummary,
    UpdateResumeBody,
    UpdateVersionBody,
    VersionDetail,
    VersionSummary,
)


class TemplateOut(ApiModel):
    id: str
    name: str
    description: str | None = None
    ats_safe: bool
    version: int


COLUMNS = ["id", "name", "description", "ats_safe", "version"]


def templates_list(request: HttpRequest):
    """Active templates in registry order (== the createdAt order the seed
    establishes). Public: the picker must render before anyone signs in."""
    if request.method != "GET":
        return not_allowed(["GET"])
    rows = Template.objects.filter(is_active=True).order_by("created_at")
    return send_data(list[TemplateOut], list(rows.values(*COLUMNS)))


class ProfileOut(ApiModel):
    content: dict[str, Any]
    updated_at: datetime | None = None


class PutProfileBody(ApiModel):
    content: ResumeContent


def _normalized(profile_row) -> dict:
    return ResumeContent.model_validate(profile_row.data).model_dump(
        mode="json", by_alias=True, exclude_none=True
    )


@require_auth
@csrf_exempt
def profile(request: HttpRequest):
    """GET reads the master profile, PUT replaces it."""
    if request.method == "GET":
        profile_row = Profile.objects.filter(user=request.user).first()
        if not profile_row:
            return send_data(ProfileOut, {"content": EMPTY_RESUME_CONTENT, "updated_at": None})
        return send_data(
            ProfileOut, {"content": _normalized(profile_row), "updated_at": profile_row.updated_at}
        )

    if request.method == "PUT":
        body = parse_body(PutProfileBody, request)
        content = body.content.model_dump(mode="json", by_alias=True, exclude_none=True)
        profile_row, _ = Profile.objects.update_or_create(
            user=request.user, defaults={"data": content}
        )
        return send_data(ProfileOut, {"content": content, "updated_at": profile_row.updated_at})

    return not_allowed(["GET", "PUT"])


@require_auth
@csrf_exempt
def resumes(request: HttpRequest):
    if request.method == "GET":
        query = parse_query(ListResumesQuery, request)
        return send_data(list[ResumeSummary], service.list_resumes(request.user.id, query.archived))
    if request.method == "POST":
        body = parse_body(CreateResumeBody, request)
        return send_data(ResumeDetail, service.create_resume(request.user, body), status=201)
    return not_allowed(["GET", "POST"])


@require_auth
@csrf_exempt
def resume_detail(request: HttpRequest, resume_id):
    if request.method == "GET":
        return send_data(ResumeDetail, service.get_resume(request.user.id, resume_id))
    if request.method == "PATCH":
        body = parse_body(UpdateResumeBody, request)
        return send_data(ResumeSummary, service.update_resume(request.user.id, resume_id, body))
    if request.method == "DELETE":
        service.delete_resume(request.user.id, resume_id)
        return HttpResponse(status=204)
    return not_allowed(["GET", "PATCH", "DELETE"])


@require_auth
@csrf_exempt
def versions(request: HttpRequest, resume_id):
    if request.method == "GET":
        query = parse_query(ListVersionsQuery, request)
        rows = service.list_versions(request.user.id, resume_id, query.limit, query.before)
        return send_data(list[VersionSummary], rows)
    if request.method == "POST":
        body = parse_body(CreateVersionBody, request)
        if body.kind == "ai":
            raise AppError(503, "AI_UNAVAILABLE", "AI suggestions are not available yet")
        return send_data(
            VersionDetail, service.create_version(request.user.id, resume_id, body), status=201
        )
    return not_allowed(["GET", "POST"])


@require_auth
@csrf_exempt
def version_detail(request: HttpRequest, resume_id, version_id):
    if request.method == "GET":
        return send_data(
            VersionDetail, service.version_row_detail(request.user.id, resume_id, version_id)
        )
    if request.method == "PATCH":
        body = parse_body(UpdateVersionBody, request)
        return send_data(
            VersionDetail, service.update_version(request.user.id, resume_id, version_id, body)
        )
    return not_allowed(["GET", "PATCH"])
