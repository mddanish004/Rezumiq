"""Request and response shapes, ported from resumes.schemas.ts.

Pydantic models take the roles the zod schemas had; wire keys stay camelCase
through ApiModel aliases.
"""

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import Field, StringConstraints, model_validator

from api.common.errors import ValidationError
from api.common.models import ApiModel
from api.common.parse import StringBool
from resumes.content import ResumeContent
from templates.layout import ResumeLayout

TexSource = Annotated[str, StringConstraints(min_length=1, max_length=200_000)]
IdParam = uuid.UUID

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Semver = Annotated[str, StringConstraints(pattern=r"^\d+\.\d+\.\d+$")]


class BlankSource(ApiModel):
    type: Literal["blank"]


class ProfileSource(ApiModel):
    type: Literal["profile"]


class ContentSource(ApiModel):
    type: Literal["content"]
    content: ResumeContent


class TexValueSource(ApiModel):
    type: Literal["tex"]
    tex_source: TexSource


class ResumeRefSource(ApiModel):
    type: Literal["resume"]
    resume_id: IdParam
    version_id: IdParam | None = None


class CustomTemplateSource(ApiModel):
    type: Literal["customTemplate"]
    custom_template_id: IdParam


ResumeSource = Annotated[
    BlankSource
    | ProfileSource
    | ContentSource
    | TexValueSource
    | ResumeRefSource
    | CustomTemplateSource,
    Field(discriminator="type"),
]


class CreateResumeBody(ApiModel):
    title: Title
    mode: Literal["structured", "code"] = "structured"
    template_id: str | None = None
    job_id: IdParam | None = None
    page_limit: Annotated[int, Field(ge=1, le=3)] = 1
    layout: ResumeLayout | None = None
    source: ResumeSource = BlankSource(type="blank")


class UpdateResumeBody(ApiModel):
    title: Title | None = None
    template_id: str | None = None
    job_id: IdParam | None = None
    page_limit: Annotated[int, Field(ge=1, le=3)] | None = None
    layout: ResumeLayout | None = None
    archived: bool | None = None
    mode: Literal["structured", "code"] | None = None

    @model_validator(mode="after")
    def _at_least_one(self):
        if not self.model_fields_set:
            raise ValidationError(
                [
                    {
                        "location": "body",
                        "path": "",
                        "message": "Provide at least one field to update",
                    }
                ]
            )
        return self


class ManualVersionBody(ApiModel):
    kind: Literal["manual"]
    base_version_id: IdParam | None = None
    content: ResumeContent | None = None
    tex_source: TexSource | None = None
    label: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)] | None
    ) = None
    semver: Semver | None = None


class RestoreVersionBody(ApiModel):
    kind: Literal["restore"]
    from_version_id: IdParam


class AiVersionBody(ApiModel):
    kind: Literal["ai"]
    suggestion_id: IdParam
    accepted_operation_ids: Annotated[list[str], Field(min_length=1)]


CreateVersionBody = Annotated[
    ManualVersionBody | RestoreVersionBody | AiVersionBody, Field(discriminator="kind")
]


class UpdateVersionBody(ApiModel):
    label: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)] | None
    ) = None
    semver: Semver | None = None

    @model_validator(mode="after")
    def _at_least_one(self):
        if not self.model_fields_set:
            raise ValidationError(
                [
                    {
                        "location": "body",
                        "path": "",
                        "message": "Provide at least one field to update",
                    }
                ]
            )
        return self


class ListResumesQuery(ApiModel):
    archived: StringBool = False


class ListVersionsQuery(ApiModel):
    limit: Annotated[int, Field(ge=1, le=100)] = 50
    before: datetime | None = None


class ResumeSummary(ApiModel):
    id: IdParam
    title: str
    mode: Literal["structured", "code"]
    template_id: str | None = None
    job_id: IdParam | None = None
    source_resume_id: IdParam | None = None
    head_version_id: IdParam | None = None
    page_limit: int
    layout: dict[str, Any]
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    latest_ats: dict[str, Any] | None = None


class VersionSummary(ApiModel):
    id: IdParam
    parent_id: IdParam | None = None
    kind: Literal["import", "manual", "ai", "restore", "named"]
    label: str | None = None
    semver: str | None = None
    created_at: datetime


class VersionDetail(VersionSummary):
    content: dict[str, Any] | None = None
    tex_source: str | None = None


class ResumeDetail(ResumeSummary):
    head: VersionDetail | None = None
