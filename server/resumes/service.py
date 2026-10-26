"""Resume and version lifecycle, ported from resumes.service.ts.

Versions are immutable snapshots: nothing ever rewrites a stored version's
content or texSource, they are only appended and re-pointed at by the
resume's head.
"""

from datetime import UTC, datetime

from django.db import transaction
from django.utils import timezone

from api.common.errors import AppError, NotFoundError, ValidationError
from resumes.content import EMPTY_RESUME_CONTENT, ResumeContent
from resumes.models import Job, Profile, Resume, ResumeVersion
from templates import find_template
from templates.layout import ResumeLayout

DEFAULT_TEMPLATE = "developer"

MODE_ISSUES = {
    "tex": [
        {
            "location": "body",
            "path": "mode",
            "message": "Pasted LaTeX creates a code-mode resume; convert it with an import",
        }
    ],
    "resume": [
        {
            "location": "body",
            "path": "mode",
            "message": "A code-mode resume can only be copied as code; convert it with an import",
        }
    ],
}


def timestamp_iso(value: datetime) -> str:
    """The old toISOString shape: UTC, always with milliseconds and a Z."""
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def layout_instance(value) -> ResumeLayout:
    """The model form for template rendering; absent/empty means defaults."""
    if isinstance(value, ResumeLayout):
        return value
    return ResumeLayout.model_validate(value or {})


def normalized_layout(value) -> dict:
    """Storage form: wire keys, spacing default filled, optional keys absent."""
    return layout_instance(value).model_dump(mode="json", by_alias=True, exclude_none=True)


def _normalized_content(value) -> dict:
    return ResumeContent.model_validate(value).model_dump(
        mode="json", by_alias=True, exclude_none=True
    )


def resume_summary(resume: Resume) -> dict:
    return {
        "id": resume.id,
        "title": resume.title,
        "mode": resume.mode,
        "template_id": resume.template_id,
        "job_id": resume.job_id,
        "source_resume_id": resume.source_resume_id,
        "head_version_id": resume.head_version_id,
        "page_limit": resume.page_limit,
        "layout": normalized_layout(resume.layout),
        "archived_at": resume.archived_at,
        "created_at": resume.created_at,
        "updated_at": resume.updated_at,
    }


def version_summary(version: ResumeVersion) -> dict:
    return {
        "id": version.id,
        "parent_id": version.parent_id,
        "kind": version.kind,
        "label": version.label,
        "semver": version.semver,
        "created_at": version.created_at,
    }


def version_detail(version: ResumeVersion) -> dict:
    detail = version_summary(version)
    detail["content"] = (
        _normalized_content(version.content) if version.content is not None else None
    )
    detail["tex_source"] = version.tex_source
    return detail


def get_owned_resume(user_id: str, resume_id, lock: bool = False) -> Resume:
    rows = Resume.objects.filter(user_id=user_id, id=resume_id, deleted_at__isnull=True)
    if lock:
        rows = rows.select_for_update()
    resume = rows.first()
    if not resume:
        raise NotFoundError("Resume")
    return resume


def get_version_row(resume_id, version_id) -> ResumeVersion:
    try:
        return ResumeVersion.objects.get(id=version_id, resume_id=resume_id)
    except ResumeVersion.DoesNotExist:
        raise NotFoundError("Version") from None


def assert_job_owned(user_id: str, job_id) -> None:
    if not Job.objects.filter(id=job_id, user_id=user_id).exists():
        raise NotFoundError("Job")


def assert_template_exists(template_id: str) -> None:
    from resumes.models import Template

    if not Template.objects.filter(id=template_id, is_active=True).exists():
        raise NotFoundError("Template")


def append_version(
    resume: Resume, kind: str, content=None, tex_source=None, label=None, semver=None
):
    content = _normalized_content(content) if content is not None else None
    if resume.mode == "structured" and content is None:
        raise ValidationError(
            [{"location": "body", "path": "content", "message": "Structured resumes need content"}]
        )
    if resume.mode == "code" and tex_source is None:
        raise ValidationError(
            [
                {
                    "location": "body",
                    "path": "texSource",
                    "message": "Code-mode resumes need texSource",
                }
            ]
        )
    version = ResumeVersion.objects.create(
        resume=resume,
        parent_id=resume.head_version_id,
        kind=kind,
        content=content,
        tex_source=tex_source,
        label=label,
        semver=semver,
    )
    Resume.objects.filter(id=resume.id).update(
        head_version_id=version.id, updated_at=timezone.now()
    )
    resume.head_version_id = version.id
    return version


def _profile_content(user_id: str) -> ResumeContent:
    row = Profile.objects.filter(user_id=user_id).first()
    if not row:
        return ResumeContent.model_validate(EMPTY_RESUME_CONTENT)
    return ResumeContent.model_validate(row.data)


def resolve_source(
    user_id: str, body, template_id: str | None
) -> tuple[ResumeContent | None, str | None, str, str | None]:
    """Returns (content, tex_source, kind, sourceResumeId) for the requested source."""
    source = body.source

    def as_mode(
        content: ResumeContent | None,
        tex_source: str | None = None,
        kind: str = "manual",
        source_id=None,
    ):
        if body.mode == "structured":
            return content, None, kind, source_id
        template = find_template(template_id or DEFAULT_TEMPLATE)
        if not template:
            raise NotFoundError("Template")
        return None, template.render(content, body.layout), kind, source_id

    if source.type == "blank":
        empty = ResumeContent.model_validate(EMPTY_RESUME_CONTENT)
        return as_mode(empty, kind="manual")
    if source.type == "profile":
        return as_mode(_profile_content(user_id), kind="import")
    if source.type == "content":
        return as_mode(source.content, kind="import")
    if source.type == "tex":
        if body.mode != "code":
            raise ValidationError(
                [{"location": "body", "path": "mode", "message": MODE_ISSUES["tex"][0]["message"]}]
            )
        return None, source.tex_source, "import", None
    if source.type == "resume":
        original = get_owned_resume(user_id, source.resume_id)
        version_id = source.version_id or original.head_version_id
        if not version_id:
            raise NotFoundError("Version")
        version = get_version_row(original.id, version_id)
        if version.content is not None:
            return as_mode(
                ResumeContent.model_validate(version.content), kind="manual", source_id=original.id
            )
        if body.mode == "structured":
            raise ValidationError(
                [
                    {
                        "location": "body",
                        "path": "mode",
                        "message": MODE_ISSUES["resume"][0]["message"],
                    }
                ]
            )
        return None, version.tex_source, "manual", original.id
    if source.type == "customTemplate":
        raise NotFoundError("Template")
    raise AppError(400, "UNREACHABLE", "Unknown resume source type")


@transaction.atomic
def create_resume(user, body) -> dict:
    from usage.quotas import assert_resume_quota

    assert_resume_quota(user.id, user.plan)
    template_id = body.template_id or (DEFAULT_TEMPLATE if body.mode == "structured" else None)
    if template_id:
        assert_template_exists(template_id)
    if body.job_id:
        assert_job_owned(user.id, body.job_id)

    content, tex_source, kind, source_resume_id = resolve_source(user.id, body, template_id)
    resume = Resume.objects.create(
        user=user,
        title=body.title,
        mode=body.mode,
        template_id=template_id if body.mode == "structured" else None,
        job_id=body.job_id,
        source_resume_id=source_resume_id,
        page_limit=body.page_limit,
        layout=normalized_layout(body.layout),
    )
    append_version(resume, kind, content, tex_source)
    return {
        **resume_summary(resume),
        "head": version_detail(ResumeVersion.objects.get(id=resume.head_version_id)),
    }


def list_resumes(user_id: str, archived: bool) -> list[dict]:
    rows = Resume.objects.filter(user_id=user_id, deleted_at__isnull=True)
    rows = (
        rows.filter(archived_at__isnull=False)
        if archived
        else rows.filter(archived_at__isnull=True)
    )
    rows = list(rows.order_by("-updated_at"))
    from ats.service import latest_for_resumes

    latest = latest_for_resumes(user_id, [row.id for row in rows])
    summaries = []
    for resume in rows:
        summary = resume_summary(resume)
        summary["latest_ats"] = latest.get(str(resume.id))
        summaries.append(summary)
    return summaries


def get_resume(user_id: str, resume_id) -> dict:
    resume = get_owned_resume(user_id, resume_id)
    head = (
        version_detail(get_version_row(resume.id, resume.head_version_id))
        if resume.head_version_id
        else None
    )
    from ats.service import latest_for_resume

    return {
        **resume_summary(resume),
        "latest_ats": latest_for_resume(user_id, resume.id),
        "head": head,
    }


def switch_mode(user_id: str, resume: Resume, mode: str) -> dict:
    """The resume keeps its template while in LaTeX, so switching back uses the same one."""
    if mode == resume.mode:
        return resume_summary(resume)
    head = get_version_row(resume.id, resume.head_version_id)
    if mode == "code":
        content = (
            ResumeContent.model_validate(head.content)
            if head.content
            else ResumeContent.model_validate(EMPTY_RESUME_CONTENT)
        )
        template = find_template(resume.template_id or DEFAULT_TEMPLATE)
        if not template:
            raise NotFoundError("Template")
        tex_source = template.render(content, layout_instance(resume.layout))
        payload = (None, tex_source, "manual", None)
        label = "Switched to LaTeX"
    else:
        raise AppError(503, "IMPORT_UNAVAILABLE", "LaTeX import is not available yet")
    with transaction.atomic():
        Resume.objects.filter(id=resume.id).update(
            mode=mode, template_id=resume.template_id or DEFAULT_TEMPLATE
        )
        resume.mode = mode
        resume.template_id = resume.template_id or DEFAULT_TEMPLATE
        version = append_version(resume, payload[2], payload[0], payload[1], label=label)
    return {**resume_summary(resume), "head": version_detail(version)}


def update_resume(user_id: str, resume_id, changes) -> dict:
    resume = get_owned_resume(user_id, resume_id)
    for field in ("title", "page_limit"):
        value = getattr(changes, field)
        if value is not None:
            setattr(resume, field, value)
    if changes.template_id:
        if resume.mode == "code":
            raise AppError(400, "TEMPLATE_NOT_ALLOWED", "Code-mode resumes don't use templates")
        assert_template_exists(changes.template_id)
        resume.template_id = changes.template_id
    if changes.layout:
        if resume.mode == "code":
            raise AppError(400, "LAYOUT_NOT_ALLOWED", "Code-mode resumes set their own layout")
        resume.layout = normalized_layout(changes.layout)
    if "job_id" in changes.model_fields_set:
        if changes.job_id:
            assert_job_owned(user_id, changes.job_id)
        resume.job_id = changes.job_id
    if changes.archived is not None:
        resume.archived_at = timezone.now() if changes.archived else None
    resume.updated_at = timezone.now()
    resume.save()

    if changes.mode and changes.mode != resume.mode:
        return switch_mode(user_id, resume, changes.mode)
    return resume_summary(resume)


def delete_resume(user_id: str, resume_id) -> None:
    resume = get_owned_resume(user_id, resume_id)
    Resume.objects.filter(id=resume.id).update(deleted_at=timezone.now())


def list_versions(
    user_id: str, resume_id, limit: int, before: datetime | None = None
) -> list[dict]:
    resume = get_owned_resume(user_id, resume_id)
    rows = ResumeVersion.objects.filter(resume_id=resume.id)
    if before:
        rows = rows.filter(created_at__lt=before)
    rows = rows.order_by("-created_at")[:limit]
    return [version_summary(version) for version in rows]


def create_version(user_id: str, resume_id, body) -> dict:
    with transaction.atomic():
        resume = get_owned_resume(user_id, resume_id, lock=True)
        kind = body.kind
        if kind == "ai":
            raise AppError(503, "AI_UNAVAILABLE", "AI suggestions are not available yet")
        if kind == "restore":
            source = get_version_row(resume.id, body.from_version_id)
            content = _normalized_content(source.content) if source.content is not None else None
            mode = "structured" if source.content is not None else "code"
            if mode != resume.mode:
                Resume.objects.filter(id=resume.id).update(mode=mode)
                resume.mode = mode
            version = append_version(
                resume,
                "restore",
                content,
                source.tex_source,
                label=f"Restored from {timestamp_iso(source.created_at)}",
            )
            return version_detail(version)

        if body.base_version_id:
            base = str(body.base_version_id)
            head = str(resume.head_version_id) if resume.head_version_id else ""
            if base != head:
                raise AppError(409, "VERSION_CONFLICT", "This resume was changed somewhere else")
        kind = "named" if body.label else "manual"
        version = append_version(
            resume, kind, body.content, body.tex_source, label=body.label, semver=body.semver
        )
        return version_detail(version)


def version_row_detail(user_id: str, resume_id, version_id) -> dict:
    resume = get_owned_resume(user_id, resume_id)
    return version_detail(get_version_row(resume.id, version_id))


def update_version(user_id: str, resume_id, version_id, changes) -> dict:
    resume = get_owned_resume(user_id, resume_id)
    version = get_version_row(resume.id, version_id)
    for field in ("label", "semver"):
        if field in changes.model_fields_set:
            setattr(version, field, getattr(changes, field))
    version.save(update_fields=["label", "semver"])
    return version_detail(version)


def tex_for_version(resume: Resume, version: ResumeVersion) -> str:
    """The LaTeX of a version as the compile endpoint uses it: a structured
    resume renders its head content through the resume's template.
    (Adopted from the pdfs module; that port adopts this in turn.)"""
    if version.content is not None:
        return render_structured(
            resume.template_id,
            ResumeContent.model_validate(version.content),
            layout_instance(resume.layout),
        )
    return version.tex_source


def render_structured(template_id: str | None, content: ResumeContent, layout=None) -> str:
    template = find_template(template_id or DEFAULT_TEMPLATE)
    if not template:
        raise NotFoundError("Template")
    return template.render(content, layout)
