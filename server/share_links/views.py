"""Share link endpoints, ported from modules/share-links."""

from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from api.common.errors import not_allowed
from api.common.guards import require_auth
from api.common.parse import parse_body
from api.common.responses import send_data

from . import service
from .schemas import (
    CreateShareLinkBody,
    ShareLinkResponse,
    ShareLinkStatsResponse,
    UpdateShareLinkBody,
)


@require_auth
@csrf_exempt
def share_links_for_resume(request: HttpRequest, resume_id):
    if request.method == "GET":
        return send_data(
            list[ShareLinkResponse], service.list_share_links(request.user.id, resume_id)
        )
    if request.method == "POST":
        body = parse_body(CreateShareLinkBody, request)
        data = body.model_dump(mode="json", by_alias=True, exclude_unset=True)
        if "pinnedVersionId" in data:
            data["pinnedVersionId"] = data["pinnedVersionId"]
        created = service.create_share_link(request.user.id, resume_id, data)
        return send_data(ShareLinkResponse, created, status=201)
    return not_allowed(["GET", "POST"])


@require_auth
@csrf_exempt
def share_link_detail(request: HttpRequest, share_link_id):
    if request.method == "GET":
        return send_data(ShareLinkResponse, service.get_share_link(request.user.id, share_link_id))
    if request.method == "PATCH":
        body = parse_body(UpdateShareLinkBody, request)
        changes = body.model_dump(mode="json", by_alias=True, exclude_unset=True)
        return send_data(
            ShareLinkResponse, service.update_share_link(request.user.id, share_link_id, changes)
        )
    if request.method == "DELETE":
        service.delete_share_link(request.user.id, share_link_id)
        return HttpResponse(status=204)
    return not_allowed(["GET", "PATCH", "DELETE"])


@require_auth
@csrf_exempt
def share_link_stats(request: HttpRequest, share_link_id):
    if request.method != "GET":
        return not_allowed(["GET"])
    return send_data(
        ShareLinkStatsResponse, service.get_share_link_stats(request.user.id, share_link_id)
    )
