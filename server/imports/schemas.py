"""Import schemas, ported from imports.schemas.ts."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from api.common.models import ApiModel
from resumes.content import ResumeContent

MAX_IMPORT_TEXT = 50_000


class UploadBody(ApiModel):
    upload_id: UUID


class TextImportBody(ApiModel):
    text: str = Field(min_length=20, max_length=MAX_IMPORT_TEXT)


CreateImportBody = UploadBody | TextImportBody


class CreateDraftBody(ApiModel):
    role: str = Field(min_length=2, max_length=100)
    notes: str = Field(min_length=40, max_length=20_000)


class MissedLine(ApiModel):
    text: str
    placed: bool


class ImportOut(ApiModel):
    content: ResumeContent
    ai_run_id: UUID
    missed: list[MissedLine] = Field(default_factory=list)
    link_style: Annotated[Literal["icon-and-name"], Field()] | None = None
