"""Public endpoints, ported from modules/public."""

import urllib.parse

from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from api.common import ratelimit
from api.common.errors import AppError, not_allowed
from api.common.responses import send_data
from latex.compile import one_at_a_time
from pdfs import service as pdfs_service

from . import service
from .schemas import (
    PublicProfileResponse,
    PublicResumeResponse,
)

SHARE_PASSWORD_LIMIT = 10
SHARE_PASSWORD_WINDOW = 10 * 60


def _share_key(username, slug) -> str:
    return f"{username}/{slug}"


def _limit_share_passwords(request, key, password, contact_password):
    if password:
        ratelimit.reject(request, "share_password", SHARE_PASSWORD_LIMIT, key)
    if contact_password:
        ratelimit.reject(request, "share_contact_password", SHARE_PASSWORD_LIMIT, key)


def _record_wrong_password(request, key, password):
    if password:
        ratelimit.hit(request, "share_password", SHARE_PASSWORD_WINDOW, key)


def _record_wrong_contact_password(request, key, contact_password):
    if contact_password:
        ratelimit.hit(request, "share_contact_password", SHARE_PASSWORD_WINDOW, key)


def _viewer_from(request):
    def h(name):
        return request.META.get(name)

    city = h("HTTP_X_SHARE_CITY")
    try:
        city = urllib.parse.unquote(city) if city else None
    except Exception:  # noqa: BLE001
        city = None
    return {
        "userId": request.user.id if getattr(request.user, "is_authenticated", False) else None,
        "visitorKey": h("HTTP_X_SHARE_VISITOR") or request.META.get("REMOTE_ADDR") or "unknown",
        "userAgent": h("HTTP_X_SHARE_USER_AGENT") or request.META.get("HTTP_USER_AGENT") or "",
        "referrer": h("HTTP_X_SHARE_REFERRER"),
        "country": h("HTTP_CF_IPCOUNTRY"),
        "region": h("HTTP_X_SHARE_REGION"),
        "city": city,
    }


@csrf_exempt
def public_profile(request: HttpRequest, username):
    if request.method != "GET":
        return not_allowed(["GET"])
    data = service.get_public_profile(username)
    return send_data(PublicProfileResponse, data)


@csrf_exempt
def public_resume(request: HttpRequest, username, slug):
    if request.method != "GET":
        return not_allowed(["GET"])
    password = request.META.get("HTTP_X_SHARE_PASSWORD")
    contact_password = request.META.get("HTTP_X_SHARE_CONTACT_PASSWORD")
    key = _share_key(username, slug)
    _limit_share_passwords(request, key, password, contact_password)
    viewer = _viewer_from(request)
    try:
        result = service.get_public_resume(username, slug, password, contact_password, viewer)
    except AppError as exc:
        if exc.code == "PASSWORD_REQUIRED":
            _record_wrong_password(request, key, password)
        raise
    data = result["data"]
    if data.get("contactLocked"):
        _record_wrong_contact_password(request, key, contact_password)
    if not result["isListed"]:
        pass
    response = send_data(PublicResumeResponse, data)
    if not result["isListed"]:
        response["X-Robots-Tag"] = "noindex, nofollow"
    return response


@csrf_exempt
def public_resume_pdf(request: HttpRequest, username, slug):
    if request.method != "GET":
        return not_allowed(["GET"])
    password = request.META.get("HTTP_X_SHARE_PASSWORD")
    contact_password = request.META.get("HTTP_X_SHARE_CONTACT_PASSWORD")
    key = _share_key(username, slug)
    _limit_share_passwords(request, key, password, contact_password)
    try:
        info = service.get_public_resume_for_pdf(username, slug, password, contact_password)
    except AppError as exc:
        if exc.code == "PASSWORD_REQUIRED":
            _record_wrong_password(request, key, password)
        raise
    resume = info["resume"]
    version = info["version"]
    if info["contact"] == "locked":
        _record_wrong_contact_password(request, key, contact_password)

    resume_dict = {
        "template_id": resume.template_id,
        "title": resume.title,
        "layout": resume.layout,
        "mode": resume.mode,
    }
    tex = pdfs_service.tex_for_version(resume_dict, version)
    user_id = resume.user_id
    result = one_at_a_time(str(user_id), lambda: pdfs_service.compile_or_throw(tex))
    pdf = result["pdf"]
    page_count = result.get("pageCount", 0)
    person = None
    if isinstance(version.get("content"), dict):
        person = (version["content"].get("basics") or {}).get("name")
    file_name = pdfs_service.pdf_file_name(person, resume.title)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{file_name}"'
    response["X-Page-Count"] = str(page_count)
    if not info["isListed"]:
        response["X-Robots-Tag"] = "noindex, nofollow"
    return response
