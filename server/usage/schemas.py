"""Usage response schema, ported from usage.routes.ts."""

from datetime import datetime

from pydantic import BaseModel, Field

from api.common.models import ApiModel


class Counter(BaseModel):
    used: int
    limit: int


class UsageOut(ApiModel):
    plan: str
    own_ai_key: bool
    period_start: datetime
    period_end: datetime
    resumes: Counter
    tailor: Counter
    edit: Counter
    import_: Counter = Field(alias="import")
    draft: Counter
    job: Counter
    ats: Counter
    review: Counter
