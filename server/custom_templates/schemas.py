"""Schemas, ported from custom-templates.schemas.ts."""

import uuid
from datetime import datetime

from pydantic import StringConstraints

from api.common.models import ApiModel

TexSource = StringConstraints(min_length=1, max_length=200_000)
Name = StringConstraints(strip_whitespace=True, min_length=1, max_length=80)


class CustomTemplateParams(ApiModel):
    custom_template_id: uuid.UUID


class CreateFromResume(ApiModel):
    type: str = "resume"
    name: str
    resume_id: uuid.UUID


class CreateFromTex(ApiModel):
    type: str = "tex"
    name: str
    tex_source: str


CreateCustomTemplateBody = CreateFromResume | CreateFromTex


class UpdateCustomTemplateBody(ApiModel):
    name: str | None = None
    tex_source: str | None = None


class CustomTemplateSummary(ApiModel):
    id: uuid.UUID
    name: str
    mode: str
    template_id: str | None = None
    created_at: datetime
    updated_at: datetime


class CustomTemplateDetail(CustomTemplateSummary):
    content: dict | None = None
    tex_source: str | None = None
