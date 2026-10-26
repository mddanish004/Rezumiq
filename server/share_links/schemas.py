"""Share link schemas, ported from share-links.schemas.ts."""

import uuid
from datetime import datetime

from pydantic import Field, model_validator

from api.common.models import ApiModel


class ShareLinkParams(ApiModel):
    share_link_id: uuid.UUID


class CreateShareLinkBody(ApiModel):
    slug: str | None = None
    pinned_version_id: uuid.UUID | None = None
    show_contact: bool = False
    is_listed: bool = False
    password: str | None = None
    contact_password: str | None = None
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def _contact_choice(self):
        if self.show_contact and self.contact_password:
            raise ValueError("Contacts are either shown or locked with a password, not both")
        return self


class UpdateShareLinkBody(ApiModel):
    slug: str | None = None
    pinned_version_id: uuid.UUID | None = None
    show_contact: bool | None = None
    is_listed: bool | None = None
    password: str | None = None
    contact_password: str | None = None
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def _contact_choice(self):
        if self.show_contact and self.contact_password:
            raise ValueError("Contacts are either shown or locked with a password, not both")
        return self


class ShareLinkResponse(ApiModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    slug: str
    url: str
    pinned_version_id: uuid.UUID | None = None
    show_contact: bool
    is_listed: bool
    has_password: bool
    has_contact_password: bool
    expires_at: datetime | None = None
    view_count: int
    last_viewed_at: datetime | None = None
    created_at: datetime


class ShareLinkStatsResponse(ApiModel):
    view_count: int
    unique_visitors: int
    last_viewed_at: datetime | None = None
    views_by_day: list[dict] = Field(default_factory=list)
    top_referrers: list[dict] = Field(default_factory=list)
    countries: list[dict] = Field(default_factory=list)
    places: list[dict] = Field(default_factory=list)
