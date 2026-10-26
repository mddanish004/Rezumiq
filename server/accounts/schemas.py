"""API models for /me and usernames, ported from users.schemas.ts."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import StringConstraints, model_validator

from api.common.models import ApiModel

from .usernames import USERNAME_PATTERN

Plan = Literal["free", "season_pass", "pro"]

Username = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_lower=True, pattern=USERNAME_PATTERN.pattern),
]


class MeOut(ApiModel):
    id: int
    name: str
    email: str
    email_verified: bool
    image: str | None = None
    username: str
    plan: Plan
    is_anonymous: bool
    is_admin: bool
    created_at: datetime


class UpdateMeBody(ApiModel):
    name: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
        | None
    ) = None
    username: Username | None = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        if self.name is None and self.username is None:
            raise ValueError("Provide at least one field to update")
        return self


class UsernameOut(ApiModel):
    username: str
    available: bool
