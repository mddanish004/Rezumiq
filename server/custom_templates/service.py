"""Custom template lifecycle, ported from modules/custom-templates."""

from __future__ import annotations

from api.common.errors import AppError, NotFoundError
from custom_templates.models import CustomTemplate
from resumes import service as resumes_service

MAX_CUSTOM_TEMPLATES = 20


def _detail(row: CustomTemplate) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "mode": row.mode,
        "template_id": row.template_id,
        "content": row.content,
        "tex_source": row.tex_source,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def list_custom_templates(user_id) -> list[dict]:
    rows = CustomTemplate.objects.filter(user_id=user_id).order_by("-updated_at")
    return [
        {
            "id": r.id,
            "name": r.name,
            "mode": r.mode,
            "template_id": r.template_id,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        }
        for r in rows
    ]


def get_custom_template(user_id, custom_template_id) -> dict:
    try:
        row = CustomTemplate.objects.get(id=custom_template_id, user_id=user_id)
    except CustomTemplate.DoesNotExist:
        raise NotFoundError("Template") from None
    return _detail(row)


def create_custom_template(user_id, data: dict) -> dict:
    count = CustomTemplate.objects.filter(user_id=user_id).count()
    if count >= MAX_CUSTOM_TEMPLATES:
        raise AppError(
            403,
            "CUSTOM_TEMPLATE_LIMIT",
            f"You can keep up to {MAX_CUSTOM_TEMPLATES} templates. Delete one to add another.",
        )

    if data.get("type") == "tex":
        row = CustomTemplate.objects.create(
            user_id=user_id,
            name=data["name"],
            mode="code",
            tex_source=data["texSource"],
        )
    else:
        resume = resumes_service.get_resume(user_id, data["resumeId"])
        head = resume.get("head")
        if not head:
            raise NotFoundError("Version")
        if head.get("content") is not None:
            row = CustomTemplate.objects.create(
                user_id=user_id,
                name=data["name"],
                mode="structured",
                template_id=resume.get("template_id") or resume.get("templateId"),
                content=head["content"],
            )
        else:
            row = CustomTemplate.objects.create(
                user_id=user_id,
                name=data["name"],
                mode="code",
                tex_source=head.get("tex_source") or head.get("texSource"),
            )
    return _detail(row)


def update_custom_template(user_id, custom_template_id, changes: dict) -> dict:
    try:
        current = CustomTemplate.objects.get(id=custom_template_id, user_id=user_id)
    except CustomTemplate.DoesNotExist:
        raise NotFoundError("Template") from None
    if changes.get("texSource") is not None and current.mode != "code":
        raise AppError(400, "TEX_NOT_ALLOWED", "Only LaTeX templates can have their code edited")
    if "name" in changes and changes["name"] is not None:
        current.name = changes["name"]
    if "texSource" in changes:
        current.tex_source = changes["texSource"]
    current.save()
    return _detail(current)


def delete_custom_template(user_id, custom_template_id) -> None:
    deleted = CustomTemplate.objects.filter(id=custom_template_id, user_id=user_id).delete()
    if deleted[0] == 0:
        raise NotFoundError("Template")
