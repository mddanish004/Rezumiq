"""Job schemas, ported from jobs.schemas.ts."""

import uuid
from datetime import datetime

from pydantic import Field

from api.common.models import ApiModel


class JobParams(ApiModel):
    job_id: uuid.UUID


class CreateJobRaw(ApiModel):
    raw_text: str = Field(min_length=50, max_length=30000)


class CreateJobUrl(ApiModel):
    source_url: str


class ParsedJob(ApiModel):
    company: str | None = None
    role: str | None = None
    seniority: str = "unknown"
    domain: str | None = None
    must_have: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class JobResponse(ApiModel):
    id: uuid.UUID
    company: str | None = None
    role: str | None = None
    source_url: str | None = None
    raw_text: str
    parsed: dict | None = None
    created_at: datetime


class JobSummary(ApiModel):
    id: uuid.UUID
    company: str | None = None
    role: str | None = None
    source_url: str | None = None
    created_at: datetime
    latest_match: dict | None = None
