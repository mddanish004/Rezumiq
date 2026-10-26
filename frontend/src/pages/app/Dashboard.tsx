import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  ArrowUpRight,
  Briefcase,
  Download,
  FilePlus2,
  Gauge,
  KeyRound,
  Plus,
  Share2,
  Sparkles,
  Upload,
} from "lucide-react";
import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from "recharts";
import { api, type AiRuns, type Analytics, type Job, type Resume, type Subscription, type Template, type Usage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatDate, formatRelative, inr, usdFromMicros } from "@/lib/utils";

export default function Dashboard() {
  const { user } = useAuth();
  const usage = useQuery<Usage>({ queryKey: ["usage"], queryFn: api.usage, retry: false });
  const subscription = useQuery<Subscription>({ queryKey: ["subscription"], queryFn: api.subscription, retry: false });
  const resumes = useQuery<Resume[]>({ queryKey: ["resumes", false], queryFn: () => api.resumes(false), retry: false });
  const jobs = useQuery<Job[]>({ queryKey: ["jobs"], queryFn: api.jobs, retry: false });
  const analytics = useQuery<Analytics>({ queryKey: ["analytics", 30], queryFn: () => api.analytics(30), retry: false });
  const aiRuns = useQuery<AiRuns>({ queryKey: ["ai-runs"], queryFn: api.aiRuns, retry: false });
  const templates = useQuery<Template[]>({ queryKey: ["templates"], queryFn: api.templates, retry: false });

  const firstName = user?.name?.trim().split(/\s+/)[0];
  const activeResumes = resumes.data ?? [];
  const savedJobs = jobs.data ?? [];
  const templateNames = new Map((templates.data ?? []).map((template) => [template.id, template.name]));
  const jobById = new Map(savedJobs.map((job) => [job.id, job]));
  const plan = usage.data?.plan ?? "free";
  const planName = plan === "season_pass" ? "Season Pass" : plan === "pro" ? "Pro" : "Free tier";
  const periodEnd = subscription.data?.subscription?.currentPeriodEnd;
  const hasData = activeResumes.length > 0 || savedJobs.length > 0;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow={`Desk session / ${new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" })}`}
        title={firstName ? `Welcome back, ${firstName}.` : "Welcome back."}
        description={
          hasData
            ? `${activeResumes.length} active ${activeResumes.length === 1 ? "resume" : "resumes"} and ${savedJobs.length} saved ${savedJobs.length === 1 ? "posting" : "postings"}. Your last checks and share activity are below.`
            : "Start with a blank page, import an existing resume, or draft one from notes. The ATS checker is open whenever you want a second opinion."
        }
        actions={
          <>
            <Link to="/app/resumes?new=1">
              <Button size="sm">
                <Plus size={14} /> New resume
              </Button>
            </Link>
            <Link to="/app/import">
              <Button size="sm" variant="secondary">
                <Upload size={14} /> Import resume
              </Button>
            </Link>
            <Link to="/app/ats">
              <Button size="sm" variant="secondary">
                <Gauge size={14} /> Check ATS score
              </Button>
            </Link>
            <Link to="/app/jobs">
              <Button size="sm" variant="secondary">
                <Briefcase size={14} /> Add job post
              </Button>
            </Link>
          </>
        }
      />

      <section className="grid gap-4 xl:grid-cols-[1.35fr_0.65fr]">
        <Card className="overflow-hidden p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="grid h-7 w-7 place-items-center rounded-full bg-lime/50">
                  <Sparkles size={14} />
                </span>
                <p className="font-display text-xl">{planName}</p>
              </div>
              <p className="mt-1.5 text-xs text-muted">
                {plan === "free"
                  ? "One AI-written resume, ATS checks, and a real LaTeX PDF."
                  : periodEnd
                    ? `${subscription.data?.subscription?.status === "cancelled" ? "Access ends" : "Renews"} ${formatDate(periodEnd)}`
                    : "Your paid plan is active."}
              </p>
            </div>
            <Link
              to="/app/usage"
              className="inline-flex items-center gap-1 text-[11px] font-medium text-muted underline decoration-line underline-offset-4 hover:text-ink"
            >
              Detailed usage <ArrowUpRight size={12} />
            </Link>
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <Meter label="AI tailors" used={usage.data?.tailor.used ?? 0} limit={usage.data?.tailor.limit ?? 1} />
            <Meter label="ATS checks" used={usage.data?.ats.used ?? 0} limit={usage.data?.ats.limit ?? 20} />
            <Meter label="AI edits" used={usage.data?.edit.used ?? 0} limit={usage.data?.edit.limit ?? 50} />
          </div>
        </Card>

        <Card className="relative overflow-hidden border-ink bg-ink p-5 text-paper">
          <div className="pointer-events-none absolute inset-0 opacity-[0.14] paper-grid" />
          <div className="relative">
            <div className="flex items-center justify-between">
              <Badge tone="lime" className="border-transparent bg-lime/15 text-lime">
                <KeyRound size={10} /> Own AI key
              </Badge>
              <span className={`h-1.5 w-1.5 rounded-full ${usage.data?.ownAiKey ? "bg-lime" : "bg-paper/30"}`} />
            </div>
            <p className="mt-5 font-display text-2xl">{usage.data?.ownAiKey ? "Connected." : "Bring your own key."}</p>
            <p className="mt-2 max-w-xs text-xs leading-5 text-paper/60">
              {usage.data?.ownAiKey
                ? "Monthly AI limits no longer apply. AI reviews still need a paid plan."
                : "Groq, OpenAI, Anthropic, or OpenRouter. Your key bypasses the monthly AI limits."}
            </p>
            <Link to="/app/settings" className="mt-5 inline-flex items-center gap-1.5 text-xs font-medium text-lime">
              {usage.data?.ownAiKey ? "Manage key" : "Add a key"} <ArrowRight size={12} />
            </Link>
          </div>
        </Card>
      </section>

      <section>
        <div className="flex items-end justify-between gap-4">
          <div>
            <h2 className="font-display text-2xl">Curated resumes</h2>
            <p className="text-xs text-muted">Every active draft, with its latest ATS check.</p>
          </div>
          <Link to="/app/resumes" className="inline-flex items-center gap-1 text-[11px] text-muted hover:text-ink">
            View all <ArrowUpRight size={12} />
          </Link>
        </div>
        {activeResumes.length ? (
          <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {activeResumes.slice(0, 3).map((resume) => {
              const template = resume.templateId ? templateNames.get(resume.templateId) : "Own LaTeX";
              const job = resume.jobId ? jobById.get(resume.jobId) : null;
              return (
                <Card key={resume.id} className="flex flex-col overflow-hidden">
                  <div className="relative border-b border-line bg-[#EDEAE2] p-4">
                    <div className="mx-auto aspect-[1.32/1] max-w-[260px] rounded border border-line bg-white px-5 py-5 document-shadow">
                      <p className="text-center font-display text-[10px] tracking-[0.02em]">ROHAN KULKARNI</p>
                      <p className="mt-0.5 text-center font-mono text-[5px] uppercase tracking-[0.12em] text-muted">
                        Bengaluru · rohan@hey.com
                      </p>
                      <div className="mt-3 space-y-1">
                        {[80, 62, 74, 58, 70, 52].map((width, index) => (
                          <div key={index} className="h-0.5 rounded bg-line" style={{ width: `${width}%` }} />
                        ))}
                      </div>
                      <div className="mt-3 space-y-1">
                        <div className="h-0.5 w-[28%] rounded bg-forest/50" />
                        {[88, 64, 76].map((width, index) => (
                          <div key={index} className="h-0.5 rounded bg-line" style={{ width: `${width}%` }} />
                        ))}
                      </div>
                      <p className="mt-3 truncate text-[6px] text-muted">{resume.title}</p>
                    </div>
                    {resume.latestAts ? (
                      <span className="absolute bottom-3 right-3 rounded bg-ink px-2 py-1 font-mono text-[9px] uppercase tracking-[0.1em] text-paper">
                        ATS {resume.latestAts.score}
                      </span>
                    ) : (
                      <span className="absolute bottom-3 right-3 rounded border border-line bg-surface px-2 py-1 font-mono text-[9px] uppercase tracking-[0.1em] text-muted">
                        Not scored
                      </span>
                    )}
                  </div>
                  <div className="flex flex-1 flex-col p-4">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-[11px] text-muted">
                        {job ? `Target: ${job.company ?? job.role ?? "Saved job"}` : "No target job"}
                      </p>
                      <span className="shrink-0 text-[10px] text-muted">{formatRelative(resume.updatedAt)}</span>
                    </div>
                    <p className="mt-0.5 truncate font-medium">{resume.title}</p>
                    <div className="mt-2 flex flex-wrap items-center gap-1.5">
                      <Badge tone={resume.mode === "code" ? "dark" : "neutral"}>
                        {resume.mode === "code" ? "LaTeX" : template}
                      </Badge>
                      <span className="font-mono text-[9px] uppercase tracking-[0.08em] text-muted">
                        Limit {resume.pageLimit} {resume.pageLimit === 1 ? "page" : "pages"}
                      </span>
                    </div>
                    <div className="mt-auto flex items-center gap-2 pt-4">
                      <Link to={`/app/resumes/${resume.id}/edit`} className="flex-1">
                        <Button size="sm" variant="secondary" className="w-full">
                          Open
                        </Button>
                      </Link>
                      <a href={api.resumePdfUrl(resume.id)} target="_blank" rel="noreferrer">
                        <Button size="sm" variant="ghost" aria-label="Download PDF">
                          <Download size={14} />
                        </Button>
                      </a>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        ) : (
          <div className="mt-4">
            <EmptyState
              icon={<FilePlus2 size={20} />}
              title="No resumes yet"
              description="Start from a template, import a PDF or LaTeX file, or draft one from rough notes."
              action={
                <Link to="/app/resumes">
                  <Button size="sm">
                    <Plus size={14} /> Create a resume
                  </Button>
                </Link>
              }
            />
          </div>
        )}
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
        <div>
          <div className="flex items-end justify-between">
            <div>
              <h2 className="font-display text-2xl">Tracked postings</h2>
              <p className="text-xs text-muted">Saved job descriptions, ready for tailoring and checks.</p>
            </div>
            <Link to="/app/jobs" className="inline-flex items-center gap-1 text-[11px] text-muted hover:text-ink">
              All jobs <ArrowUpRight size={12} />
            </Link>
          </div>
          <div className="mt-4 space-y-3">
            {savedJobs.length ? (
              savedJobs.slice(0, 3).map((job) => (
                <Card key={job.id} className="flex flex-wrap items-center gap-4 p-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">
                        {(job.company || "Saved posting").slice(0, 30)}
                      </p>
                      {job.latestMatch ? (
                        <Badge tone="success">{job.latestMatch.percent}% match</Badge>
                      ) : (
                        <Badge tone="outline">Not checked</Badge>
                      )}
                    </div>
                    <p className="mt-1 truncate text-sm font-medium">{job.role || "Job description"}</p>
                    <p className="mt-0.5 text-xs text-muted">{job.sourceUrl ? "From a URL" : "Pasted description"}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Link to={`/app/jobs`}>
                      <Button size="sm" variant="ghost">
                        Tailor
                      </Button>
                    </Link>
                    <Link to="/app/ats">
                      <Button size="sm" variant="secondary">
                        Check ATS
                      </Button>
                    </Link>
                  </div>
                </Card>
              ))
            ) : (
              <EmptyState
                icon={<Briefcase size={20} />}
                title="No saved postings"
                description="Save a job description once and reuse it for tailoring, ATS checks, and coverage."
                action={
                  <Link to="/app/jobs">
                    <Button size="sm" variant="secondary">
                      Add a job post
                    </Button>
                  </Link>
                }
              />
            )}
          </div>
        </div>

        <Card className="p-5">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="font-display text-xl">Share activity</h2>
              <p className="text-xs text-muted">Rolling 30-day link engagement.</p>
            </div>
            <Badge tone="lime">
              <Share2 size={10} /> Live links
            </Badge>
          </div>
          <div className="mt-5 flex items-end gap-2">
            <p className="font-display text-4xl leading-none">{analytics.data?.totals.views ?? 0}</p>
            <p className="pb-1 text-xs text-muted">views</p>
            <p className="ml-auto pb-1 text-xs text-muted">
              {analytics.data?.totals.uniqueVisitors ?? 0} unique visitors
            </p>
          </div>
          <div className="mt-2 h-28">
            {analytics.data && analytics.data.viewsByDay?.some((day) => day.views > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={analytics.data.viewsByDay}>
                  <defs>
                    <linearGradient id="viewsFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#1F5A46" stopOpacity={0.25} />
                      <stop offset="100%" stopColor="#1F5A46" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="day" hide />
                  <Tooltip
                    contentStyle={{
                      borderRadius: 8,
                      border: "1px solid #E3DFD6",
                      fontSize: 12,
                      background: "#fff",
                    }}
                    labelFormatter={(value) => formatDate(String(value))}
                  />
                  <Area
                    type="monotone"
                    dataKey="views"
                    stroke="#1F5A46"
                    strokeWidth={2}
                    fill="url(#viewsFill)"
                    dot={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center rounded-field border border-dashed border-line text-xs text-muted">
                No views yet. Create a share link from a resume.
              </div>
            )}
          </div>
          <div className="mt-4 border-t border-line pt-3">
            <p className="font-mono text-[9px] uppercase tracking-[0.14em] text-muted">Channel attribution</p>
            <div className="mt-2 flex h-1.5 overflow-hidden rounded-full bg-soft">
              {(analytics.data?.referrers?.length ? analytics.data.referrers : [{ label: "Direct", views: 1 }])
                .slice(0, 3)
                .map((source, index) => (
                  <span
                    key={source.label}
                    className={index === 0 ? "bg-ink" : index === 1 ? "bg-forest" : "bg-line"}
                    style={{
                      width: `${Math.max(
                        4,
                        (source.views /
                          (analytics.data?.referrers?.reduce((sum, item) => sum + item.views, 0) || 1)) *
                          100,
                      )}%`,
                    }}
                  />
                ))}
            </div>
            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[10px] text-muted">
              {(analytics.data?.referrers?.length ? analytics.data.referrers : [{ label: "Direct", views: 0 }])
                .slice(0, 3)
                .map((source, index) => (
                  <span key={source.label} className="inline-flex items-center gap-1.5">
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${
                        index === 0 ? "bg-ink" : index === 1 ? "bg-forest" : "bg-line"
                      }`}
                    />
                    {source.label}
                  </span>
                ))}
            </div>
          </div>
        </Card>
      </section>

      <section>
        <div className="flex items-end justify-between">
          <div>
            <h2 className="font-display text-2xl">AI telemetry</h2>
            <p className="text-xs text-muted">The last 20 runs. No prompts, outputs, or resume text.</p>
          </div>
          <Link to="/app/usage" className="inline-flex items-center gap-1 text-[11px] text-muted hover:text-ink">
            Detailed logs <ArrowUpRight size={12} />
          </Link>
        </div>
        <Card className="mt-4 grid gap-5 p-5 lg:grid-cols-[1.1fr_0.9fr_0.9fr]">
          <div>
            <p className="font-mono text-[9px] uppercase tracking-[0.14em] text-muted">Success consistency</p>
            <p className="mt-2 font-display text-2xl">
              {aiRuns.data?.runs.filter((run) => run.status === "succeeded").length ?? 0}
              <span className="text-base text-muted"> / {aiRuns.data?.runs.length ?? 0} runs</span>
            </p>
            <div className="mt-3 flex flex-wrap gap-1">
              {(aiRuns.data?.runs ?? []).slice(0, 20).map((run) => (
                <span
                  key={run.id}
                  title={`${run.step}: ${run.status}`}
                  className={`h-4 w-4 rounded-[4px] border ${
                    run.status === "succeeded"
                      ? "border-forest/20 bg-lime"
                      : run.status === "failed"
                        ? "border-danger/20 bg-danger/15"
                        : "border-line bg-soft"
                  }`}
                />
              ))}
              {!aiRuns.data?.runs.length ? (
                <span className="text-xs text-muted">No AI runs yet.</span>
              ) : null}
            </div>
          </div>
          <div className="border-line lg:border-l lg:pl-5">
            <p className="font-mono text-[9px] uppercase tracking-[0.14em] text-muted">Consumed tokens</p>
            <p className="mt-2 font-display text-2xl">
              {(aiRuns.data?.runs.reduce((sum, run) => sum + run.inputTokens + run.outputTokens, 0) ?? 0).toLocaleString("en-IN")}
            </p>
            <p className="mt-1 text-[11px] text-muted">Across the last 20 runs</p>
          </div>
          <div className="border-line lg:border-l lg:pl-5">
            <p className="font-mono text-[9px] uppercase tracking-[0.14em] text-muted">Estimated spend</p>
            <p className="mt-2 font-display text-2xl">
              {usdFromMicros(aiRuns.data?.monthCostUsdMicros ?? 0)}
            </p>
            <p className="mt-1 text-[11px] text-muted">
              {aiRuns.data?.monthUnpricedRuns
                ? `${aiRuns.data.monthUnpricedRuns} unpriced runs this month`
                : "This calendar month, where prices are known"}
            </p>
          </div>
        </Card>
      </section>

      <section className="flex flex-wrap items-center justify-between gap-3 rounded-card border border-line bg-surface px-5 py-4">
        <div>
          <p className="text-sm font-medium">One more thing before the next application.</p>
          <p className="text-xs text-muted">
            The ATS report is free on every plan. Run it before you send the PDF.
          </p>
        </div>
        <div className="flex gap-2">
          <Link to="/app/ats">
            <Button size="sm" variant="secondary">
              Open ATS checker
            </Button>
          </Link>
          <Link to="/#pricing">
            <Button size="sm">
              Compare plans <ArrowRight size={13} />
            </Button>
          </Link>
        </div>
      </section>

      {plan === "free" ? (
        <p className="text-center text-[11px] text-muted">
          Free tier: {inr(0)}. Upgrade when the AI limits start to matter. Prices exclude taxes.
        </p>
      ) : null}
    </div>
  );
}

function Meter({ label, used, limit }: { label: string; used: number; limit: number }) {
  const percent = Math.min(100, Math.round((used / Math.max(1, limit)) * 100));
  return (
    <div className="rounded-field border border-line bg-paper/60 p-3">
      <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">{label}</p>
      <p className="mt-1 text-lg font-medium">
        {used} <span className="text-xs font-normal text-muted">/ {limit}</span>
      </p>
      <div className="mt-2 h-1 overflow-hidden rounded-full bg-line">
        <div className={`h-full rounded-full ${percent > 85 ? "bg-warning" : "bg-ink"}`} style={{ width: `${percent}%` }} />
      </div>
      <p className="mt-1.5 text-[10px] text-muted">{Math.max(0, limit - used)} remaining</p>
    </div>
  );
}
