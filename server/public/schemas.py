"""Public module schemas."""

from datetime import datetime

from pydantic import Field

from api.common.models import ApiModel


class PublicUserParams(ApiModel):
    username: str


class PublicResumeParams(ApiModel):
    username: str
    slug: str


class PublicProfileResponse(ApiModel):
    username: str
    name: str
    image: str | None = None
    resumes: list[dict] = Field(default_factory=list)


class PublicResumeResponse(ApiModel):
    username: str
    slug: str
    title: str
    mode: str
    template_id: str | None = None
    content: dict | None = None
    contact_masked: bool
    contact_locked: bool
    updated_at: datetime
