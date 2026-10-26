"""ATS request and response shapes, ported from ats.schemas.ts."""

import uuid
from typing import Annotated, Any, Literal

from pydantic import Field, StringConstraints

from api.common.models import ApiModel

IdParam = uuid.UUID

TextItem = Annotated[
    dict,
    Field(description="One pdf.js text run with coordinates"),
]


class CreateResumeAtsReportBody(ApiModel):
    job_id: IdParam | None = None


class CreateAtsReportBody(ApiModel):
    text: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=200, max_length=50_000)
    ]
    job_description: Annotated[
        str | None, StringConstraints(strip_whitespace=True, max_length=20_000)
    ] = None
    items: list[TextItem] | None = Field(default=None, max_length=6000)
    page: dict[str, int | float] | None = None
    file: dict[str, Any] | None = None


class CreateAtsReviewBody(ApiModel):
    text: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=200, max_length=50_000)
    ]
    job_description: Annotated[
        str | None, StringConstraints(strip_whitespace=True, max_length=20_000)
    ] = None


class CheckLine(ApiModel):
    text: str
    highlight: str | None = None


class Check(ApiModel):
    id: str
    label: str
    status: Literal["pass", "warn", "fail"]
    detail: str
    fix: str | None = None
    lines: list[CheckLine] | None = None


class Category(ApiModel):
    id: str
    label: str
    score: int
    max_score: int
    checks: list[Check]


class SkillLists(ApiModel):
    matched: list[str]
    missing: list[str]


class Keywords(ApiModel):
    matched: list[str]
    missing: list[str]
    hard: SkillLists
    soft: SkillLists
    must_have_missing: list[str]
    implied: list[dict[str, str]]


class TitleMatch(ApiModel):
    job_title: str
    best: str | None
    level: Literal["exact", "close", "none"]


class ParseReport(ApiModel):
    parse_rate: float | None
    fields: list[dict]


class Knockout(ApiModel):
    id: str
    label: str
    requirement: str
    required: bool
    status: Literal["met", "not-met", "unclear", "not-on-resume"]
    evidence: str | None
    advice: str
    checked_with_ai: bool


class Stats(ApiModel):
    words: int
    bullets: int
    sections: list[str]
    quantified_bullets: int


class AtsReport(ApiModel):
    score: int
    grade: Literal["excellent", "good", "fair", "poor"]
    summary: str
    categories: list[Category]
    keywords: Keywords | None = None
    title: TitleMatch | None = None
    parse: ParseReport | None = None
    knockouts: list[Knockout] | None = None
    stats: Stats


class AtsReview(ApiModel):
    verdict: str
    strengths: list[str]
    fixes: list[dict[str, str | None]]
    job_fit: dict[str, Any] | None = None
