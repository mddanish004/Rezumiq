"""AI run history schema, ported from ai-runs.routes.ts."""

from datetime import datetime
from uuid import UUID

from api.common.models import ApiModel


class AiRunRow(ApiModel):
    id: UUID
    created_at: datetime
    step: str
    status: str
    model: str
    byok: bool
    input_tokens: int
    output_tokens: int
    cost_usd_micros: int | None
    latency_ms: int | None
    resume_id: UUID | None


class AiRunListOut(ApiModel):
    period_start: datetime
    month_cost_usd_micros: int
    month_unpriced_runs: int
    runs: list[AiRunRow]
