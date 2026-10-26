"""Share links, ported from modules/share-links."""

from __future__ import annotations

import re

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models import Count

from api.common.errors import AppError, ConflictError, NotFoundError
from resumes.models import Resume, ResumeVersion
from share_links.models import LinkView, ShareLink

SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,28}[a-z0-9])$")


def _slugify(value: str) -> str:
    import unicodedata

    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:40] or "resume"


def _username(user_id) -> str:
    return get_user_model().objects.get(id=user_id).username


def _detail(link: ShareLink) -> dict:
    return {
        "id": link.id,
        "resume_id": link.resume_id,
        "slug": link.slug,
        "url": f"{_frontend_url()}/{_username(link.user_id)}/{link.slug}",
        "pinned_version_id": link.pinned_version_id,
        "show_contact": link.show_contact,
        "is_listed": link.is_listed,
        "has_password": bool(link.password_hash),
        "has_contact_password": bool(link.contact_password_hash),
        "expires_at": link.expires_at,
        "view_count": link.view_count,
        "last_viewed_at": link.last_viewed_at,
        "created_at": link.created_at,
    }


def _frontend_url() -> str:
    from django.conf import settings

    return getattr(settings, "FRONTEND_URL", "http://localhost:5173")


def _assert_version_of_resume(resume_id, version_id) -> None:
    if not ResumeVersion.objects.filter(id=version_id, resume_id=resume_id).exists():
        raise NotFoundError("Version")


def _assert_contact_lock_allowed(mode: str) -> None:
    if mode == "code":
        raise AppError(
            400,
            "CONTACT_LOCK_UNAVAILABLE",
            "LaTeX resumes show their contact lines, so they can't lock them",
        )


def _slug_taken(user_id, slug, except_id=None) -> bool:
    qs = ShareLink.objects.filter(user_id=user_id, slug=slug, deleted_at__isnull=True)
    if except_id:
        qs = qs.exclude(id=except_id)
    return qs.exists()


def _unique_slug(user_id, base: str) -> str:
    root = _slugify(base)
    if len(root) < 3:
        root = "resume"
    if not _slug_taken(user_id, root):
        return root
    for n in range(2, 100):
        candidate = f"{root[:26]}-{n}"
        if not _slug_taken(user_id, candidate):
            return candidate
    raise ConflictError("Could not generate a free slug; pick one yourself")


def list_share_links(user_id, resume_id) -> list[dict]:
    rows = ShareLink.objects.filter(
        user_id=user_id, resume_id=resume_id, deleted_at__isnull=True
    ).order_by("-created_at")
    return [_detail(r) for r in rows]


def get_share_link(user_id, share_link_id) -> dict:
    try:
        row = ShareLink.objects.get(id=share_link_id, user_id=user_id, deleted_at__isnull=True)
    except ShareLink.DoesNotExist:
        raise NotFoundError("Share link") from None
    return _detail(row)


def create_share_link(user_id, resume_id, data: dict) -> dict:
    resume = None

    try:
        resume = Resume.objects.get(id=resume_id, user_id=user_id, deleted_at__isnull=True)
    except Resume.DoesNotExist:
        raise NotFoundError("Resume") from None

    contact_password = data.get("contactPassword") or data.get("contact_password")
    if contact_password:
        _assert_contact_lock_allowed(resume.mode)

    pinned = data.get("pinnedVersionId") or data.get("pinned_version_id")
    if pinned:
        _assert_version_of_resume(resume.id, pinned)

    slug = data.get("slug")
    if slug:
        if not SLUG_RE.match(slug):
            raise AppError(400, "VALIDATION_ERROR", "Use 3-30 lowercase letters, digits or hyphens")
        if _slug_taken(user_id, slug):
            raise ConflictError("You already use this slug")
    else:
        slug = _unique_slug(user_id, resume.title)

    password = data.get("password")
    contact_pw = contact_password
    link = ShareLink.objects.create(
        user_id=user_id,
        resume_id=resume.id,
        slug=slug,
        pinned_version_id=pinned,
        show_contact=bool(data.get("showContact", data.get("show_contact", False))),
        is_listed=bool(data.get("isListed", data.get("is_listed", False))),
        password_hash=make_password(password) if password else None,
        contact_password_hash=make_password(contact_pw) if contact_pw else None,
        expires_at=data.get("expiresAt") or data.get("expires_at"),
    )
    return _detail(link)


def update_share_link(user_id, share_link_id, changes: dict) -> dict:
    try:
        link = ShareLink.objects.get(id=share_link_id, user_id=user_id, deleted_at__isnull=True)
    except ShareLink.DoesNotExist:
        raise NotFoundError("Share link") from None

    resume = None

    resume = Resume.objects.get(id=link.resume_id)

    if changes.get("contactPassword") is not None or changes.get("contact_password") is not None:
        _assert_contact_lock_allowed(resume.mode)

    slug = changes.get("slug")
    if slug is not None:
        if not SLUG_RE.match(slug):
            raise AppError(400, "VALIDATION_ERROR", "Use 3-30 lowercase letters, digits or hyphens")
        if _slug_taken(user_id, slug, except_id=link.id):
            raise ConflictError("You already use this slug")
        link.slug = slug

    if "pinnedVersionId" in changes or "pinned_version_id" in changes:
        pv = changes.get("pinnedVersionId", changes.get("pinned_version_id"))
        if pv:
            _assert_version_of_resume(link.resume_id, pv)
        link.pinned_version_id = pv

    if "showContact" in changes or "show_contact" in changes:
        link.show_contact = bool(changes.get("showContact", changes.get("show_contact")))
    if "isListed" in changes or "is_listed" in changes:
        link.is_listed = bool(changes.get("isListed", changes.get("is_listed")))

    if "password" in changes:
        pw = changes["password"]
        link.password_hash = make_password(pw) if pw else None
    if "contactPassword" in changes or "contact_password" in changes:
        cpw = changes.get("contactPassword", changes.get("contact_password"))
        link.contact_password_hash = make_password(cpw) if cpw else None

    if "expiresAt" in changes or "expires_at" in changes:
        link.expires_at = changes.get("expiresAt", changes.get("expires_at"))

    link.save()
    return _detail(link)


def delete_share_link(user_id, share_link_id) -> None:
    deleted = ShareLink.objects.filter(
        id=share_link_id, user_id=user_id, deleted_at__isnull=True
    ).delete()
    if deleted[0] == 0:
        raise NotFoundError("Share link")


def get_share_link_stats(user_id, share_link_id) -> dict:
    try:
        link = ShareLink.objects.get(id=share_link_id, user_id=user_id, deleted_at__isnull=True)
    except ShareLink.DoesNotExist:
        raise NotFoundError("Share link") from None

    views = LinkView.objects.filter(share_link=link)
    unique = views.values("visitor_hash").distinct().count()
    from django.db.models.functions import TruncDate

    by_day_qs = (
        views.annotate(day=TruncDate("viewed_at"))
        .values("day")
        .annotate(views=Count("id"))
        .order_by("day")
    )
    views_by_day = [{"day": str(r["day"]), "views": r["views"]} for r in by_day_qs]

    ref_qs = (
        views.exclude(referrer__isnull=True)
        .exclude(referrer="")
        .values("referrer")
        .annotate(views=Count("id"))
        .order_by("-views")[:10]
    )
    top_referrers = [{"referrer": r["referrer"], "views": r["views"]} for r in ref_qs]

    country_qs = (
        views.exclude(country__isnull=True)
        .exclude(country="")
        .values("country")
        .annotate(views=Count("id"))
        .order_by("-views")
    )
    countries = [{"country": r["country"], "views": r["views"]} for r in country_qs]

    place_qs = (
        views.values("city", "region", "country").annotate(views=Count("id")).order_by("-views")
    )
    places = [
        {"city": r["city"], "region": r["region"], "country": r["country"], "views": r["views"]}
        for r in place_qs
    ]

    return {
        "view_count": link.view_count,
        "unique_visitors": unique,
        "last_viewed_at": link.last_viewed_at,
        "views_by_day": views_by_day,
        "top_referrers": top_referrers,
        "countries": countries,
        "places": places,
    }
