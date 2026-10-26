import type { Content, Layout, Version, VersionDetail } from "./resume";

const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  code?: string;
  details?: unknown;

  constructor(status: number, message: string, code?: string, details?: unknown) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  allow401?: boolean;
};

function readCookie(name: string) {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1];
}

let csrfPrimed = false;

export async function primeCsrf() {
  if (csrfPrimed || readCookie("csrftoken")) {
    csrfPrimed = true;
    return;
  }
  await fetch(`${API_URL}/_allauth/browser/v1/config`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  csrfPrimed = true;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method ?? "GET";
  const unsafe = !["GET", "HEAD", "OPTIONS"].includes(method);
  if (unsafe) await primeCsrf();
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...options.headers,
  };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (unsafe) {
    const token = readCookie("csrftoken");
    if (token) headers["X-CSRFToken"] = decodeURIComponent(token);
  }

  const response = await fetch(`${API_URL}${path}`, {
    method,
    credentials: "include",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  const text = await response.text();
  let payload: unknown = null;
  try {
    payload = text ? JSON.parse(text) : null;
  } catch {
    payload = text;
  }

  const unwrap = path.startsWith("/v1/");

  if (!response.ok) {
    const apiError = (payload as { error?: { code?: string; message?: string; details?: unknown } })?.error;
    const allauthError = payload as { errors?: Array<{ message?: string }>; detail?: string };
    const message =
      apiError?.message ??
      allauthError?.errors?.[0]?.message ??
      allauthError?.detail ??
      `Request failed (${response.status})`;
    if (!(options.allow401 && response.status === 401)) {
      throw new ApiError(response.status, message, apiError?.code, apiError?.details);
    }
    return payload as T;
  }
  if (unwrap && payload && typeof payload === "object" && "data" in payload) {
    return (payload as { data: T }).data;
  }
  return payload as T;
}

export type Plan = "free" | "season_pass" | "pro";

export type Me = {
  id: number;
  name: string;
  email: string;
  emailVerified: boolean;
  image: string | null;
  username: string;
  plan: Plan;
  isAnonymous: boolean;
  isAdmin: boolean;
  createdAt: string;
};

export type Counter = { used: number; limit: number };

export type Usage = {
  plan: Plan;
  ownAiKey: boolean;
  periodStart: string;
  periodEnd: string;
  resumes: Counter;
  tailor: Counter;
  edit: Counter;
  import: Counter;
  draft: Counter;
  job: Counter;
  ats: Counter;
  review: Counter;
};

export type Subscription = {
  plan: Plan;
  subscription: {
    id: string;
    plan: "season_pass" | "pro";
    status: "created" | "active" | "past_due" | "cancelled" | "expired";
    currentPeriodEnd: string | null;
    cancelledAt: string | null;
  } | null;
};

export type ResumeDetail = Resume & {
  head: {
    id: string;
    kind: string;
    label: string | null;
    semver: string | null;
    content: Record<string, unknown> | null;
    texSource: string | null;
    createdAt: string;
  } | null;
};

export type RefundQuote = {
  quote: {
    paymentId: string;
    plan: "season_pass" | "pro" | null;
    amountPaidPaise: number;
    feePaise: number;
    refundPaise: number;
    refundableUntil: string;
  } | null;
  reason: string | null;
};

export type Checkout = {
  provider: "dodo";
  sessionId: string;
  checkoutUrl: string;
  plan: "season_pass" | "pro";
  amountPaise: number;
  currency: "INR";
};

export type LatestAts = {
  score: number;
  grade: "excellent" | "good" | "fair" | "poor";
  jobId: string | null;
  checkedAt: string;
};

export type Resume = {
  id: string;
  title: string;
  mode: "structured" | "code";
  templateId: string | null;
  jobId: string | null;
  sourceResumeId: string | null;
  headVersionId: string | null;
  pageLimit: number;
  layout: { spacing: "compact" | "normal" | "relaxed"; fontSize?: 10 | 11 | 12; links?: string };
  archivedAt: string | null;
  createdAt: string;
  updatedAt: string;
  latestAts?: LatestAts | null;
};

export type Job = {
  id: string;
  company: string | null;
  role: string | null;
  sourceUrl: string | null;
  createdAt: string;
  latestMatch?: {
    percent: number;
    resumeId: string;
    checkedAt: string;
  } | null;
};

export type Template = {
  id: string;
  name: string;
  description: string | null;
  atsSafe: boolean;
  version: number;
};

export type Analytics = {
  days: number;
  totals: {
    views: number;
    uniqueVisitors: number;
    previousViews: number;
    previousUniqueVisitors: number;
  };
  viewsByDay: Array<{ day: string; views: number }>;
  links: Array<{
    id: string;
    slug: string;
    resumeId: string;
    resumeTitle: string;
    views: number;
    totalViews: number;
    lastViewedAt: string | null;
  }>;
  referrers: Array<{ label: string; views: number }>;
  countries: Array<{ label: string; views: number }>;
  cities: Array<{ label: string; views: number }>;
  devices: Array<{ label: string; views: number }>;
  recentViews: Array<{
    id: string;
    viewedAt: string;
    shareLinkId: string;
    slug: string;
    resumeTitle: string;
    referrer: string | null;
    country: string | null;
    device: string | null;
  }>;
};

export type AiRun = {
  id: string;
  createdAt: string;
  step: string;
  status: "pending" | "succeeded" | "failed";
  model: string;
  byok: boolean;
  inputTokens: number;
  outputTokens: number;
  costUsdMicros: number | null;
  latencyMs: number | null;
  resumeId: string | null;
};

export type AiRuns = {
  periodStart: string;
  monthCostUsdMicros: number;
  monthUnpricedRuns: number;
  runs: AiRun[];
};

export type AtsCheck = {
  id: string;
  label: string;
  status: "pass" | "warn" | "fail";
  detail: string;
  fix: string | null;
  lines?: Array<{ text: string; highlight: string | null }> | null;
};

export type AtsCategory = {
  id: string;
  label: string;
  score: number;
  maxScore: number;
  checks: AtsCheck[];
};

export type AtsReportData = {
  score: number;
  grade: "excellent" | "good" | "fair" | "poor";
  summary: string;
  categories: AtsCategory[];
  keywords: {
    matched: string[];
    missing: string[];
    hard: { matched: string[]; missing: string[] };
    soft: { matched: string[]; missing: string[] };
    mustHaveMissing: string[];
    implied: Array<{ skill: string; evidence: string }>;
  } | null;
  title: { jobTitle: string; best: string | null; level: string } | null;
  parse: { parseRate: number | null; fields: Array<Record<string, unknown>> } | null;
  knockouts: Array<{
    id: string;
    label: string;
    requirement: string;
    required: boolean;
    status: string;
    evidence: string | null;
    advice: string;
    checkedWithAi: boolean;
  }> | null;
  stats: { words: number; bullets: number; sections: string[]; quantifiedBullets: number };
};

export type SuggestionOperation = {
  id: string;
  type: string;
  reason: string;
  flags: string[];
  bulletId?: string | null;
  afterBulletId?: string | null;
  targetId?: string | null;
  parentId?: string | null;
  groupId?: string | null;
  text?: string | null;
  hidden?: boolean | null;
  points?: number | null;
  orderedIds?: string[] | null;
  items?: string[] | null;
  texSource?: string | null;
};

export type Suggestion = {
  id: string;
  type: "tailor" | "edit" | "fix_compile";
  status: "pending" | "applied";
  baseVersionId: string;
  appliedVersionId: string | null;
  summary: string;
  operations: SuggestionOperation[];
  model: string;
  byok: boolean;
  costUsdMicros: number | null;
  createdAt: string;
};

export type AiKey = {
  provider: "groq" | "openai" | "anthropic" | "openrouter";
  enabled: boolean;
  modelId: string | null;
  modelIds: string[];
  keyHint: string;
  verifiedAt: string;
};

export type UploadedFile = {
  id: string;
  kind: "pdf" | "tex" | "text";
  fileName: string;
  mimeType: string;
  sizeBytes: number;
  createdAt: string;
};

export type ImportResult = {
  content: Content;
  aiRunId: string;
  missed: Array<{ text: string; placed: boolean }>;
  linkStyle: "icon-and-name" | null;
};

export type ShareLink = {
  id: string;
  resumeId: string;
  slug: string;
  url: string;
  pinnedVersionId: string | null;
  showContact: boolean;
  isListed: boolean;
  hasPassword: boolean;
  hasContactPassword: boolean;
  expiresAt: string | null;
  viewCount: number;
  lastViewedAt: string | null;
  createdAt: string;
};

export type ShareStats = {
  viewCount: number;
  uniqueVisitors: number;
  lastViewedAt: string | null;
  viewsByDay: Array<{ day: string; views: number }>;
  topReferrers: Array<{ label: string; views: number }>;
  countries: Array<{ label: string; views: number }>;
  places: Array<{ label: string; views: number }>;
};

export type PublicProfile = {
  username: string;
  name: string;
  image: string | null;
  resumes: Array<{ slug: string; title: string; hasPassword: boolean; updatedAt: string }>;
};

export type PublicResume = {
  username: string;
  slug: string;
  title: string;
  mode: "structured" | "code";
  templateId: string | null;
  content: Content | null;
  contactMasked: boolean;
  contactLocked: boolean;
  updatedAt: string;
};

export type CoverageCheck = {
  requirement: string;
  status: "covered" | "in_profile" | "missing";
  foundIn: string[];
};

export type CoverageReport = {
  covered: number;
  total: number;
  mustHave: CoverageCheck[];
  niceToHave: CoverageCheck[];
  keywords: CoverageCheck[];
};

export type AdminLabelCount = { label: string; count: number };

export type AdminOverview = {
  days: number;
  totals: {
    users: number;
    guests: number;
    newUsers: number;
    previousNewUsers: number;
    activeUsers: number;
    previousActiveUsers: number;
    paidUsers: number;
    suspendedUsers: number;
    resumes: number;
    resumesCreated: number;
    previousResumesCreated: number;
    aiRuns: number;
    previousAiRuns: number;
    aiFailed: number;
    aiCostUsdMicros: number;
    previousAiCostUsdMicros: number;
    revenuePaise: number;
    previousRevenuePaise: number;
    shareViews: number;
    previousShareViews: number;
  };
  byDay: Array<{ day: string; signups: number; resumes: number; aiRuns: number; views: number }>;
  plans: AdminLabelCount[];
  providers: AdminLabelCount[];
  funnel: { signedUp: number; createdResume: number; usedAi: number; shared: number; paid: number };
  recentSignups: Array<{
    id: number;
    name: string;
    email: string;
    image: string | null;
    plan: Plan;
    createdAt: string;
    providers: string[];
  }>;
};

export type AdminUserRow = {
  id: number;
  name: string;
  email: string;
  image: string | null;
  username: string;
  plan: Plan;
  isAnonymous: boolean;
  suspendedAt: string | null;
  createdAt: string;
  lastActiveAt: string | null;
  providers: string[];
  resumes: number;
  aiRuns: number;
};

export type AdminUsersPage = {
  users: AdminUserRow[];
  page: number;
  pageSize: number;
  total: number;
};

export type AdminUserDetail = {
  user: {
    id: number;
    name: string;
    email: string;
    emailVerified: boolean;
    image: string | null;
    username: string;
    plan: Plan;
    isAnonymous: boolean;
    suspendedAt: string | null;
    createdAt: string;
    updatedAt: string;
  };
  accounts: Array<{ providerId: string; createdAt: string }>;
  resumes: Array<{
    id: string;
    title: string;
    mode: "structured" | "code";
    templateId: string | null;
    createdAt: string;
    updatedAt: string;
    archivedAt: string | null;
    deletedAt: string | null;
    versions: number;
  }>;
  ai: {
    runs: number;
    byokRuns: number;
    costUsdMicros: number;
    lastRunAt: string | null;
    bySteps: Array<{ step: string; runs: number; failed: number; costUsdMicros: number }>;
  };
  usage: {
    plan: Plan;
    ownAiKey: boolean;
    periodStart: string;
    periodEnd: string;
    resumes: Counter;
    tailor: Counter;
    edit: Counter;
    import: Counter;
    draft: Counter;
  };
  subscriptions: Array<{
    id: string;
    plan: "season_pass" | "pro";
    status: "created" | "active" | "past_due" | "cancelled" | "expired";
    currentPeriodStart: string | null;
    currentPeriodEnd: string | null;
    dodoSubscriptionId: string | null;
    complimentary: boolean;
    createdAt: string;
  }>;
  payments: Array<{
    id: string;
    amountPaise: number;
    status: "created" | "captured" | "failed" | "refunded";
    method: string | null;
    dodoPaymentId: string | null;
    createdAt: string;
  }>;
  sessions: Array<{
    id: string;
    createdAt: string;
    updatedAt: string;
    expiresAt: string;
    userAgent: string | null;
  }>;
  shareLinks: number;
  shareViews: number;
  jobs: number;
};

export type AdminAi = {
  days: number;
  totals: {
    runs: number;
    failed: number;
    byok: number;
    costUsdMicros: number;
    inputTokens: number;
    cachedInputTokens: number;
    outputTokens: number;
    users: number;
  };
  bySteps: Array<{
    step: string;
    runs: number;
    failed: number;
    costUsdMicros: number;
    p50Ms: number;
    p95Ms: number;
  }>;
  byModels: Array<{ model: string; runs: number; costUsdMicros: number; tokens: number }>;
  byDay: Array<{ day: string; runs: number; costUsdMicros: number }>;
  failures: Array<{
    id: string;
    createdAt: string;
    step: string;
    model: string;
    error: string | null;
    userId: number;
    email: string;
  }>;
  topUsers: Array<{ userId: number; email: string; name: string; runs: number; costUsdMicros: number }>;
};

export type AdminRevenue = {
  days: number;
  totals: {
    paise: number;
    previousPaise: number;
    allTimePaise: number;
    payers: number;
    checkouts: number;
    checkoutsPaid: number;
  };
  byDay: Array<{ day: string; paise: number }>;
  activeSubscriptions: Array<{ plan: "season_pass" | "pro"; active: number }>;
  statuses: AdminLabelCount[];
  payments: Array<{
    id: string;
    createdAt: string;
    amountPaise: number;
    status: "created" | "captured" | "failed" | "refunded";
    method: string | null;
    dodoPaymentId: string | null;
    plan: "season_pass" | "pro" | null;
    userId: number;
    email: string;
  }>;
  dodoConfigured: boolean;
};

export type AdminContent = {
  days: number;
  resumes: {
    total: number;
    live: number;
    archived: number;
    deleted: number;
    structured: number;
    code: number;
    tailored: number;
  };
  byTemplate: AdminLabelCount[];
  versionKinds: AdminLabelCount[];
  sharing: { links: number; listed: number; protected: number; plain: number; views: number };
  topLinks: Array<{
    id: string;
    slug: string;
    username: string;
    resumeTitle: string;
    views: number;
    totalViews: number;
  }>;
  customTemplates: number;
  jobs: number;
  jobsFromUrl: number;
  uploads: { files: number; bytes: number; pdf: number; tex: number; text: number };
};

export type AdminSystem = {
  api: {
    nodeVersion: string;
    uptimeSeconds: number;
    rssBytes: number;
    heapUsedBytes: number;
    environment: string;
  };
  database: {
    version: string;
    sizeBytes: number;
    latencyMs: number;
    connections: Array<{ state: string; count: number }>;
    tables: Array<{ name: string; rows: number; sizeBytes: number }>;
  };
  compiler: { mode: string; ok: boolean; latencyMs: number | null };
  backup: { key: string; sizeBytes: number; modifiedAt: string } | null;
  lastWebhookAt: string | null;
  integrations: Array<{ name: string; configured: boolean }>;
};

export type AdminTraffic = {
  configured: boolean;
  dashboardUrl: string;
  error: string | null;
  data: unknown | null;
};

export type AuthSession = {
  meta?: { is_authenticated?: boolean };
  data?: { user?: { id: number; email: string; display?: string } };
};

export function csrfToken() {
  const token = readCookie("csrftoken");
  return token ? decodeURIComponent(token) : "";
}

export async function previewPdf(
  body: { templateId: string; content: Content; layout: Layout } | { texSource: string },
  signal?: AbortSignal,
): Promise<{ blob: Blob; pageCount: number }> {
  await primeCsrf();
  const headers: Record<string, string> = { Accept: "application/pdf", "Content-Type": "application/json" };
  const token = readCookie("csrftoken");
  if (token) headers["X-CSRFToken"] = decodeURIComponent(token);
  const response = await fetch(`${API_URL}/v1/previews`, {
    method: "POST",
    credentials: "include",
    headers,
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok) {
    const text = await response.text();
    let message = `Preview failed (${response.status})`;
    try {
      const parsed = JSON.parse(text) as { error?: { message?: string } };
      message = parsed.error?.message ?? message;
    } catch {}
    throw new ApiError(response.status, message);
  }
  return {
    blob: await response.blob(),
    pageCount: Number(response.headers.get("X-Page-Count") ?? 0),
  };
}

async function errorFromResponse(response: Response, fallback: string) {
  const text = await response.text();
  try {
    const parsed = JSON.parse(text) as { error?: { code?: string; message?: string } };
    if (parsed.error?.message) {
      return new ApiError(response.status, parsed.error.message, parsed.error.code);
    }
  } catch {}
  return new ApiError(response.status, fallback);
}

export async function uploadFile(file: File): Promise<UploadedFile> {
  await primeCsrf();
  const form = new FormData();
  form.append("file", file);
  const headers: Record<string, string> = { Accept: "application/json" };
  const token = readCookie("csrftoken");
  if (token) headers["X-CSRFToken"] = decodeURIComponent(token);
  const response = await fetch(`${API_URL}/v1/uploads`, {
    method: "POST",
    credentials: "include",
    headers,
    body: form,
  });
  if (!response.ok) throw await errorFromResponse(response, `Upload failed (${response.status})`);
  const payload = (await response.json()) as { data: UploadedFile };
  return payload.data;
}

export async function publicPdfBlob(username: string, slug: string, password?: string, contactPassword?: string) {
  const headers: Record<string, string> = { Accept: "application/pdf" };
  if (password) headers["X-Share-Password"] = password;
  if (contactPassword) headers["X-Share-Contact-Password"] = contactPassword;
  const response = await fetch(
    `${API_URL}/v1/public/users/${encodeURIComponent(username)}/resumes/${encodeURIComponent(slug)}/pdf`,
    { credentials: "include", headers },
  );
  if (!response.ok) throw await errorFromResponse(response, `PDF failed (${response.status})`);
  return response.blob();
}

export const api = {
  url: API_URL,
  me: () => request<Me>("/v1/me"),
  usage: () => request<Usage>("/v1/usage"),
  subscription: () => request<Subscription>("/v1/subscription"),
  cancelSubscription: () => request<Subscription>("/v1/subscription", { method: "DELETE" }),
  createCheckout: (plan: "season_pass" | "pro") =>
    request<Checkout>("/v1/checkouts", { method: "POST", body: { plan } }),
  refundQuote: () => request<RefundQuote>("/v1/refunds/quote"),
  redeemPromo: (code: string) =>
    request<{ id: string; plan: "season_pass" | "pro"; status: string }>("/v1/promo-redemptions", {
      method: "POST",
      body: { code },
    }),
  updateMe: (body: { name?: string; username?: string }) =>
    request<Me>("/v1/me", { method: "PATCH", body }),
  usernameAvailable: (username: string) =>
    request<{ username: string; available: boolean }>(`/v1/usernames/${encodeURIComponent(username)}`),
  deleteMe: () => request<null>("/v1/me", { method: "DELETE" }),
  dataExportUrl: () => `${API_URL}/v1/me/data`,
  aiKeys: () => request<AiKey[]>("/v1/me/ai-keys"),
  putAiKey: (provider: string, apiKey: string, modelId?: string) =>
    request<AiKey>(`/v1/me/ai-keys/${provider}`, {
      method: "PUT",
      body: { apiKey, modelId: modelId || null },
    }),
  updateAiKey: (provider: string, body: { enabled?: boolean; modelId?: string }) =>
    request<AiKey>(`/v1/me/ai-keys/${provider}`, { method: "PATCH", body }),
  deleteAiKey: (provider: string) =>
    request<null>(`/v1/me/ai-keys/${provider}`, { method: "DELETE" }),
  requestRefund: (paymentId: string) =>
    request<{ paymentId: string; refundPaise: number; dodoRefundId: string }>("/v1/refunds", {
      method: "POST",
      body: { paymentId },
    }),
  resumes: (archived = false) => request<Resume[]>(`/v1/resumes?archived=${archived}`),
  resume: (id: string) => request<ResumeDetail>(`/v1/resumes/${id}`),
  jobs: () => request<Job[]>("/v1/jobs"),
  templates: () => request<Template[]>("/v1/templates"),
  analytics: (days = 30) => request<Analytics>(`/v1/analytics?days=${days}`),
  aiRuns: () => request<AiRuns>("/v1/me/ai-runs"),
  publicAts: (text: string, jobDescription?: string) =>
    request<AtsReportData>("/v1/ats-reports", {
      method: "POST",
      body: { text, jobDescription: jobDescription || null },
    }),
  createResume: (title: string, templateId?: string, mode: "structured" | "code" = "structured") =>
    request<Resume>("/v1/resumes", {
      method: "POST",
      body: { title, mode, templateId: templateId ?? null, source: { type: "blank" } },
    }),
  createResumeFromContent: (
    title: string,
    content: Content,
    templateId?: string,
    layout?: Layout,
  ) =>
    request<Resume>("/v1/resumes", {
      method: "POST",
      body: {
        title,
        mode: "structured",
        templateId: templateId ?? null,
        ...(layout ? { layout } : {}),
        source: { type: "content", content },
      },
    }),
  createResumeFromTex: (title: string, texSource: string) =>
    request<Resume>("/v1/resumes", {
      method: "POST",
      body: { title, mode: "code", source: { type: "tex", texSource } },
    }),
  importResume: (body: { uploadId: string } | { text: string }) =>
    request<ImportResult>("/v1/imports", { method: "POST", body }),
  draftResume: (role: string, notes: string) =>
    request<ImportResult>("/v1/resume-drafts", { method: "POST", body: { role, notes } }),
  profile: () => request<{ content: Content; updatedAt: string | null }>("/v1/profile"),
  saveProfile: (content: Content) =>
    request<{ content: Content; updatedAt: string | null }>("/v1/profile", {
      method: "PUT",
      body: { content },
    }),
  shareLinks: (resumeId: string) => request<ShareLink[]>(`/v1/resumes/${resumeId}/share-links`),
  createShareLink: (
    resumeId: string,
    body: Partial<{
      slug: string;
      showContact: boolean;
      isListed: boolean;
      password: string | null;
      contactPassword: string | null;
      expiresAt: string | null;
      pinnedVersionId: string | null;
    }>,
  ) => request<ShareLink>(`/v1/resumes/${resumeId}/share-links`, { method: "POST", body }),
  updateShareLink: (id: string, body: Record<string, unknown>) =>
    request<ShareLink>(`/v1/share-links/${id}`, { method: "PATCH", body }),
  deleteShareLink: (id: string) => request<null>(`/v1/share-links/${id}`, { method: "DELETE" }),
  shareStats: (id: string) => request<ShareStats>(`/v1/share-links/${id}/stats`),
  coverage: (resumeId: string, jobId: string, versionId?: string) =>
    request<CoverageReport>(
      `/v1/resumes/${resumeId}/coverage?jobId=${jobId}${versionId ? `&versionId=${versionId}` : ""}`,
    ),
  adminOverview: (days = 30) => request<AdminOverview>(`/v1/admin/overview?days=${days}`),
  adminUsers: (params: { q?: string; plan?: string; status?: string; page?: number }) => {
    const search = new URLSearchParams();
    if (params.q) search.set("q", params.q);
    if (params.plan) search.set("plan", params.plan);
    if (params.status) search.set("status", params.status);
    search.set("page", String(params.page ?? 1));
    return request<AdminUsersPage>(`/v1/admin/users?${search.toString()}`);
  },
  adminUser: (id: number) => request<AdminUserDetail>(`/v1/admin/users/${id}`),
  adminSetSuspended: (id: number, suspended: boolean) =>
    request<AdminUserDetail>(`/v1/admin/users/${id}`, { method: "PATCH", body: { suspended } }),
  adminRevokeSessions: (id: number) =>
    request<null>(`/v1/admin/users/${id}/sessions`, { method: "DELETE" }),
  adminResetUsage: (id: number) =>
    request<null>(`/v1/admin/users/${id}/usage`, { method: "DELETE" }),
  adminGrantSubscription: (id: number, plan: "season_pass" | "pro", months: number) =>
    request<AdminUserDetail>(`/v1/admin/users/${id}/subscriptions`, {
      method: "POST",
      body: { plan, months },
    }),
  adminRevokeSubscription: (id: number, subscriptionId: string) =>
    request<null>(`/v1/admin/users/${id}/subscriptions/${subscriptionId}`, { method: "DELETE" }),
  adminAi: (days = 30) => request<AdminAi>(`/v1/admin/ai?days=${days}`),
  adminRevenue: (days = 30) => request<AdminRevenue>(`/v1/admin/revenue?days=${days}`),
  adminContent: (days = 30) => request<AdminContent>(`/v1/admin/content?days=${days}`),
  adminSystem: () => request<AdminSystem>("/v1/admin/system"),
  adminTraffic: () => request<AdminTraffic>("/v1/admin/traffic"),
  publicProfile: (username: string) =>
    request<PublicProfile>(`/v1/public/users/${encodeURIComponent(username)}`),
  publicResume: (username: string, slug: string, password?: string, contactPassword?: string) =>
    request<PublicResume>(
      `/v1/public/users/${encodeURIComponent(username)}/resumes/${encodeURIComponent(slug)}`,
      {
        headers: {
          ...(password ? { "X-Share-Password": password } : {}),
          ...(contactPassword ? { "X-Share-Contact-Password": contactPassword } : {}),
        },
      },
    ),
  archiveResume: (id: string, archived: boolean) =>
    request<Resume>(`/v1/resumes/${id}`, { method: "PATCH", body: { archived } }),
  deleteResume: (id: string) => request<null>(`/v1/resumes/${id}`, { method: "DELETE" }),
  createJob: (rawText: string) =>
    request<Job>("/v1/jobs", { method: "POST", body: { rawText } }),
  createJobFromUrl: (sourceUrl: string) =>
    request<Job>("/v1/jobs", { method: "POST", body: { sourceUrl } }),
  deleteJob: (id: string) => request<null>(`/v1/jobs/${id}`, { method: "DELETE" }),
  resumePdfUrl: (id: string, versionId?: string) =>
    `${API_URL}/v1/resumes/${id}/pdf${versionId ? `?versionId=${versionId}` : ""}`,
  updateResume: (id: string, body: Partial<{ title: string; templateId: string; jobId: string | null; pageLimit: number; layout: Layout; archived: boolean; mode: "structured" | "code" }>) =>
    request<Resume>(`/v1/resumes/${id}`, { method: "PATCH", body }),
  versions: (id: string) => request<Version[]>(`/v1/resumes/${id}/versions?limit=50`),
  version: (id: string, versionId: string) =>
    request<VersionDetail>(`/v1/resumes/${id}/versions/${versionId}`),
  createVersion: (
    id: string,
    body: {
      kind: "manual";
      baseVersionId: string | null;
      content?: Content;
      texSource?: string;
      label?: string | null;
      semver?: string | null;
    },
  ) => request<VersionDetail>(`/v1/resumes/${id}/versions`, { method: "POST", body }),
  restoreVersion: (id: string, fromVersionId: string) =>
    request<VersionDetail>(`/v1/resumes/${id}/versions`, {
      method: "POST",
      body: { kind: "restore", fromVersionId },
    }),
  updateVersion: (id: string, versionId: string, body: { label?: string | null; semver?: string | null }) =>
    request<VersionDetail>(`/v1/resumes/${id}/versions/${versionId}`, { method: "PATCH", body }),
  createSuggestion: (
    id: string,
    body:
      | { type: "tailor"; jobId: string; instructions?: string }
      | { type: "edit"; instruction: string; targetIds?: string[] }
      | { type: "fix_compile" },
  ) => request<Suggestion>(`/v1/resumes/${id}/suggestions`, { method: "POST", body }),
  applySuggestion: (id: string, suggestionId: string, acceptedOperationIds: string[]) =>
    request<{ version: VersionDetail; suggestion: Suggestion }>(
      `/v1/resumes/${id}/suggestions/${suggestionId}/apply`,
      { method: "POST", body: { acceptedOperationIds } },
    ),
  atsReport: (id: string, jobId?: string) =>
    request<AtsReportData>(`/v1/resumes/${id}/ats-reports`, {
      method: "POST",
      body: { jobId: jobId || null },
    }),
  session: () => request<AuthSession>("/_allauth/browser/v1/auth/session", { allow401: true }),
  login: (email: string, password: string) =>
    request<AuthSession>("/_allauth/browser/v1/auth/login", { method: "POST", body: { email, password } }),
  signup: (email: string, password: string) =>
    request<AuthSession>("/_allauth/browser/v1/auth/signup", { method: "POST", body: { email, password } }),
  logout: () => request<AuthSession>("/_allauth/browser/v1/auth/session", { method: "DELETE" }),
  requestPasswordReset: (email: string) =>
    request<unknown>("/_allauth/browser/v1/auth/password/request", { method: "POST", body: { email } }),
  verifyEmail: (key: string) =>
    request<unknown>("/_allauth/browser/v1/auth/email/verify", {
      method: "POST",
      body: { key },
      allow401: true,
    }),
  resetPassword: (key: string, password: string) =>
    request<unknown>("/_allauth/browser/v1/auth/password/reset", {
      method: "POST",
      body: { key, password },
      allow401: true,
    }),
  googleRedirect: () => {
    const callback = `${window.location.origin}/auth/callback?next=${encodeURIComponent("/app")}`;
    const params = new URLSearchParams({ provider: "google", callback_url: callback });
    return `${API_URL}/_allauth/browser/v1/auth/provider/redirect?${params.toString()}`;
  },
};
