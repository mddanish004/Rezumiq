"""Admin response schemas, ported from admin.schemas.ts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from api.common.models import ApiModel

Plan = Literal["free", "season_pass", "pro"]
PaidPlan = Literal["season_pass", "pro"]


class AdminRangeQuery(ApiModel):
    days: int = 30
    time_zone: str = "Asia/Kolkata"


class AdminUsersQuery(ApiModel):
    q: str | None = Field(default=None, max_length=100)
    plan: Plan | None = None
    status: Literal["active", "suspended", "guest"] | None = None
    page: int = Field(default=1, ge=1)


class AdminContentQuery(ApiModel):
    days: int = 30


class AdminUserParams(ApiModel):
    user_id: int


class AdminSubscriptionParams(ApiModel):
    subscription_id: UUID


class LabelCount(ApiModel):
    label: str
    count: int


class OverviewTotals(ApiModel):
    users: int
    guests: int
    new_users: int
    previous_new_users: int
    active_users: int
    previous_active_users: int
    paid_users: int
    suspended_users: int
    resumes: int
    resumes_created: int
    previous_resumes_created: int
    ai_runs: int
    previous_ai_runs: int
    ai_failed: int
    ai_cost_usd_micros: int
    previous_ai_cost_usd_micros: int
    revenue_paise: int
    previous_revenue_paise: int
    share_views: int
    previous_share_views: int


class OverviewDay(ApiModel):
    day: str
    signups: int
    resumes: int
    ai_runs: int
    views: int


class Funnel(ApiModel):
    signed_up: int
    created_resume: int
    used_ai: int
    shared: int
    paid: int


class RecentSignup(ApiModel):
    id: int
    name: str
    email: str
    image: str | None
    plan: Plan
    created_at: datetime
    providers: list[str]


class AdminOverviewOut(ApiModel):
    days: int
    totals: OverviewTotals
    by_day: list[OverviewDay]
    plans: list[LabelCount]
    providers: list[LabelCount]
    funnel: Funnel
    recent_signups: list[RecentSignup]


class UserListRow(ApiModel):
    id: int
    name: str
    email: str
    image: str | None
    username: str
    plan: Plan
    is_anonymous: bool
    suspended_at: datetime | None
    created_at: datetime
    last_active_at: datetime | None
    providers: list[str]
    resumes: int
    ai_runs: int


class AdminUserListOut(ApiModel):
    users: list[UserListRow]
    page: int
    page_size: int
    total: int


class DetailUser(ApiModel):
    id: int
    name: str
    email: str
    email_verified: bool
    image: str | None
    username: str
    plan: Plan
    is_anonymous: bool
    suspended_at: datetime | None
    created_at: datetime
    updated_at: datetime


class LinkedAccount(ApiModel):
    provider_id: str
    created_at: datetime


class DetailResume(ApiModel):
    id: UUID
    title: str
    mode: Literal["structured", "code"]
    template_id: str | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    deleted_at: datetime | None
    versions: int


class AiStep(ApiModel):
    step: str
    runs: int
    failed: int
    cost_usd_micros: int


class DetailAi(ApiModel):
    runs: int
    byok_runs: int
    cost_usd_micros: int
    last_run_at: datetime | None
    by_steps: list[AiStep]


class Counter(ApiModel):
    used: int
    limit: int


class Usage(ApiModel):
    plan: Plan
    own_ai_key: bool
    period_start: datetime
    period_end: datetime
    resumes: Counter
    tailor: Counter
    edit: Counter
    import_: Counter = Field(alias="import")
    draft: Counter


class SubscriptionRow(ApiModel):
    id: UUID
    plan: PaidPlan
    status: Literal["created", "active", "past_due", "cancelled", "expired"]
    current_period_start: datetime | None
    current_period_end: datetime | None
    dodo_subscription_id: str | None
    complimentary: bool
    created_at: datetime


class PaymentRow(ApiModel):
    id: UUID
    amount_paise: int
    status: Literal["created", "captured", "failed", "refunded"]
    method: str | None
    dodo_payment_id: str | None
    created_at: datetime


class SessionRow(ApiModel):
    id: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    user_agent: str | None


class AdminUserOut(ApiModel):
    user: DetailUser
    accounts: list[LinkedAccount]
    resumes: list[DetailResume]
    ai: DetailAi
    usage: Usage
    subscriptions: list[SubscriptionRow]
    payments: list[PaymentRow]
    sessions: list[SessionRow]
    share_links: int
    share_views: int
    jobs: int


class UpdateAdminUserBody(ApiModel):
    suspended: bool


class CreateAdminSubscriptionBody(ApiModel):
    plan: PaidPlan
    months: int = Field(ge=1, le=24)


class AiTotals(ApiModel):
    runs: int
    failed: int
    byok: int
    cost_usd_micros: int
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    users: int


class AiStepStat(ApiModel):
    step: str
    runs: int
    failed: int
    cost_usd_micros: int
    p50_ms: int
    p95_ms: int


class AiModelStat(ApiModel):
    model: str
    runs: int
    cost_usd_micros: int
    tokens: int


class AiDay(ApiModel):
    day: str
    runs: int
    cost_usd_micros: int


class AiFailure(ApiModel):
    id: UUID
    created_at: datetime
    step: str
    model: str
    error: str | None
    user_id: int
    email: str


class AiTopUser(ApiModel):
    user_id: int
    email: str
    name: str
    runs: int
    cost_usd_micros: int


class AdminAiOut(ApiModel):
    days: int
    totals: AiTotals
    by_steps: list[AiStepStat]
    by_models: list[AiModelStat]
    by_day: list[AiDay]
    failures: list[AiFailure]
    top_users: list[AiTopUser]


class RevenueTotals(ApiModel):
    paise: int
    previous_paise: int
    all_time_paise: int
    payers: int
    checkouts: int
    checkouts_paid: int


class RevenueDay(ApiModel):
    day: str
    paise: int


class ActiveSubscription(ApiModel):
    plan: PaidPlan
    active: int


class RevenuePayment(ApiModel):
    id: UUID
    created_at: datetime
    amount_paise: int
    status: Literal["created", "captured", "failed", "refunded"]
    method: str | None
    dodo_payment_id: str | None
    plan: PaidPlan | None
    user_id: int
    email: str


class AdminRevenueOut(ApiModel):
    days: int
    totals: RevenueTotals
    by_day: list[RevenueDay]
    active_subscriptions: list[ActiveSubscription]
    statuses: list[LabelCount]
    payments: list[RevenuePayment]
    dodo_configured: bool


class ContentResumes(ApiModel):
    total: int
    live: int
    archived: int
    deleted: int
    structured: int
    code: int
    tailored: int


class ContentSharing(ApiModel):
    links: int
    listed: int
    protected: int
    plain: int
    views: int


class TopLink(ApiModel):
    id: UUID
    slug: str
    username: str
    resume_title: str
    views: int
    total_views: int


class ContentUploads(ApiModel):
    files: int
    bytes: int
    pdf: int
    tex: int
    text: int


class AdminContentOut(ApiModel):
    days: int
    resumes: ContentResumes
    by_template: list[LabelCount]
    version_kinds: list[LabelCount]
    sharing: ContentSharing
    top_links: list[TopLink]
    custom_templates: int
    jobs: int
    jobs_from_url: int
    uploads: ContentUploads


class SystemApi(ApiModel):
    node_version: str
    uptime_seconds: int
    rss_bytes: int
    heap_used_bytes: int
    environment: str


class DbConnection(ApiModel):
    state: str
    count: int


class DbTable(ApiModel):
    name: str
    rows: int
    size_bytes: int


class SystemDatabase(ApiModel):
    version: str
    size_bytes: int
    latency_ms: int
    connections: list[DbConnection]
    tables: list[DbTable]


class CompilerHealth(ApiModel):
    mode: Literal["in-process", "service"]
    ok: bool
    latency_ms: int | None


class Backup(ApiModel):
    key: str
    size_bytes: int
    modified_at: datetime


class Integration(ApiModel):
    name: str
    configured: bool


class AdminSystemOut(ApiModel):
    api: SystemApi
    database: SystemDatabase
    compiler: CompilerHealth
    backup: Backup | None
    last_webhook_at: datetime | None
    integrations: list[Integration]


class TrafficData(ApiModel):
    pass


class AdminTrafficOut(ApiModel):
    configured: bool
    dashboard_url: str
    error: str | None
    data: TrafficData | None
