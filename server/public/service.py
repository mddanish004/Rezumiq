"""Public resume pages, ported from modules/public."""

from __future__ import annotations

import hashlib
import hmac
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.utils import timezone

from api.common.errors import AppError, NotFoundError
from resumes import service as resumes_service
from share_links.models import LinkView, ShareLink

User = get_user_model()

BOT_PATTERN = re.compile(
    r"bot|crawler|spider|preview|facebookexternalhit|slurp|headless", re.IGNORECASE
)


def _place(value):
    if not value:
        return None
    v = re.sub(r"[^\w .,'-]", "", value, flags=re.UNICODE).strip()[:80]
    return v or None


def _resolve_user(username):
    from accounts.models import UsernameRedirect

    try:
        user = User.objects.get(username=username, suspended_at__isnull=True)
        return user
    except User.DoesNotExist:
        pass
    redirect = UsernameRedirect.objects.filter(old_username=username).select_related("user").first()
    if redirect and redirect.user and not redirect.user.suspended_at:
        return redirect.user
    raise NotFoundError("User")


def mask_contact(content):
    if not content:
        return content
    if isinstance(content, dict):
        basics = dict(content.get("basics", {}))
        basics.pop("email", None)
        basics.pop("phone", None)
        return {**content, "basics": basics}
    return content


def contact_access(link, owner_plan, contact_password):
    if link.show_contact:
        return "shown"
    if not link.contact_password_hash or owner_plan == "free":
        return "hidden"
    if contact_password and check_password(contact_password, link.contact_password_hash):
        return "shown"
    return "locked"


def get_public_profile(username):
    user = _resolve_user(username)
    listed = (
        ShareLink.objects.filter(user=user, is_listed=True, deleted_at__isnull=True)
        .filter(resume__deleted_at__isnull=True)
        .select_related("resume")
    )
    from django.utils import timezone as tz

    active = [l for l in listed if l.expires_at is None or l.expires_at > tz.now()]
    resumes_out = []
    for link in active:
        resumes_out.append(
            {
                "slug": link.slug,
                "title": link.resume.title,
                "hasPassword": bool(link.password_hash),
                "updatedAt": link.resume.updated_at,
            }
        )
    resumes_out.sort(key=lambda r: r["updatedAt"], reverse=True)
    return {
        "username": user.username,
        "name": getattr(user, "name", "") or user.username,
        "image": getattr(user, "image", None),
        "resumes": resumes_out,
    }


def _resolve_link(username, slug, password, contact_password):
    user = _resolve_user(username)
    link = (
        ShareLink.objects.filter(user=user, slug=slug, deleted_at__isnull=True)
        .select_related("resume")
        .first()
    )
    if not link or link.resume.deleted_at is not None:
        raise NotFoundError("Resume")
    if link.expires_at is not None and link.expires_at <= timezone.now():
        raise AppError(410, "LINK_EXPIRED", "This link has expired")
    if link.password_hash and not (password and check_password(password, link.password_hash)):
        raise AppError(401, "PASSWORD_REQUIRED", "This resume is password protected")

    resume = link.resume
    version_id = link.pinned_version_id or resume.head_version_id
    if not version_id:
        raise NotFoundError("Resume")
    version = resumes_service.version_row_detail(user.id, resume.id, version_id)
    contact = contact_access(link, getattr(user, "plan", "free"), contact_password)
    content = version.get("content")
    if content is not None and contact != "shown":
        content = mask_contact(content)
    version = {**version, "content": content}
    return user, link, resume, version, contact


def _record_view(link, viewer):
    if viewer.get("userId") is not None and str(viewer["userId"]) == str(link.user_id):
        return
    ua = viewer.get("userAgent") or ""
    if BOT_PATTERN.search(ua):
        return
    day = timezone.now().date().isoformat()
    visitor_key = viewer.get("visitorKey") or "unknown"
    visitor_hash = hmac.new(
        (getattr(settings, "SECRET_KEY", "") or "").encode(),
        f"{visitor_key}|{ua}|{day}".encode(),
        hashlib.sha256,
    ).hexdigest()
    device = (
        "tablet"
        if re.search(r"ipad|tablet", ua, re.IGNORECASE)
        else ("mobile" if re.search(r"mobile|android|iphone", ua, re.IGNORECASE) else "desktop")
    )
    referrer = None
    r = viewer.get("referrer")
    if r:
        try:
            from urllib.parse import urlparse

            referrer = urlparse(r).hostname
        except Exception:  # noqa: BLE001
            referrer = None
    LinkView.objects.create(
        share_link=link,
        visitor_hash=visitor_hash,
        referrer=referrer,
        country=(viewer.get("country") or "")[:2].upper() or None,
        region=_place(viewer.get("region")),
        city=_place(viewer.get("city")),
        device=device,
    )
    ShareLink.objects.filter(id=link.id).update(
        view_count=link.view_count + 1, last_viewed_at=timezone.now()
    )


def get_public_resume(username, slug, password, contact_password, viewer):
    user, link, resume, version, contact = _resolve_link(username, slug, password, contact_password)
    if contact_password is None:
        _record_view(link, viewer)
    return {
        "data": {
            "username": user.username,
            "slug": link.slug,
            "title": resume.title,
            "mode": resume.mode,
            "templateId": resume.template_id,
            "content": version.get("content"),
            "contactMasked": contact != "shown",
            "contactLocked": contact == "locked",
            "updatedAt": resume.updated_at,
        },
        "isListed": link.is_listed,
    }


def get_public_resume_for_pdf(username, slug, password, contact_password):
    _user, link, resume, version, contact = _resolve_link(
        username, slug, password, contact_password
    )
    return {"resume": resume, "version": version, "isListed": link.is_listed, "contact": contact}
