"""Analytics schemas."""

from pydantic import Field

from api.common.models import ApiModel


class AnalyticsQuery(ApiModel):
    days: int = 30
    time_zone: str = "Asia/Kolkata"


class AnalyticsTotals(ApiModel):
    views: int = 0
    unique_visitors: int = 0
    previous_views: int = 0
    previous_unique_visitors: int = 0


class AnalyticsResponse(ApiModel):
    days: int
    totals: AnalyticsTotals
    views_by_day: list[dict] = Field(default_factory=list)
    links: list[dict] = Field(default_factory=list)
    referrers: list[dict] = Field(default_factory=list)
    countries: list[dict] = Field(default_factory=list)
    cities: list[dict] = Field(default_factory=list)
    devices: list[dict] = Field(default_factory=list)
    recent_views: list[dict] = Field(default_factory=list)
