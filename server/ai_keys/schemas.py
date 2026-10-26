"""AI key schemas."""

from datetime import datetime

from pydantic import Field

from api.common.models import ApiModel


class AiKeyResponse(ApiModel):
    provider: str
    enabled: bool
    model_id: str | None = None
    model_ids: list[str] = Field(default_factory=list)
    key_hint: str
    verified_at: datetime


class UpdateAiKeyBody(ApiModel):
    enabled: bool | None = None
    model_id: str | None = None
