"""Suggestion schemas."""

import uuid
from datetime import datetime

from pydantic import Field

from api.common.models import ApiModel
from resumes.schemas import VersionDetail


class SuggestionParams(ApiModel):
    resume_id: uuid.UUID
    suggestion_id: uuid.UUID


class CreateSuggestionBody(ApiModel):
    type: str
    job_id: uuid.UUID | None = None
    instructions: str | None = None
    instruction: str | None = None
    target_ids: list[str] | None = None


class ApplySuggestionBody(ApiModel):
    accepted_operation_ids: list[str] = Field(default_factory=list)


class OperationResponse(ApiModel):
    id: str
    type: str
    reason: str
    flags: list[str] = Field(default_factory=list)
    bullet_id: str | None = None
    after_bullet_id: str | None = None
    target_id: str | None = None
    parent_id: str | None = None
    group_id: str | None = None
    text: str | None = None
    hidden: bool | None = None
    points: int | None = None
    ordered_ids: list[str] | None = None
    items: list[str] | None = None
    tex_source: str | None = None


class SuggestionResponse(ApiModel):
    id: uuid.UUID
    type: str
    status: str
    base_version_id: uuid.UUID
    applied_version_id: uuid.UUID | None = None
    summary: str
    operations: list[OperationResponse]
    model: str
    byok: bool = False
    cost_usd_micros: int | None = None
    created_at: datetime


class ApplySuggestionOut(ApiModel):
    version: VersionDetail
    suggestion: SuggestionResponse
