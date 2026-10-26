import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertCircle, ArrowRight, CheckCircle2, Circle, Gauge, ListChecks, Target, XCircle } from "lucide-react";
import { api, ApiError, type AtsCategory, type AtsReportData, type CoverageCheck, type Job, type Resume } from "@/lib/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { cn } from "@/lib/utils";

type Tab = "check" | "coverage";

export default function AppAts() {
  const [tab, setTab] = useState<Tab>("check");
  const resumes = useQuery<Resume[]>({ queryKey: ["resumes", false], queryFn: () => api.resumes(false) });
  const jobs = useQuery<Job[]>({ queryKey: ["jobs"], queryFn: api.jobs });
  const [resumeId, setResumeId] = useState("");
  const [jobId, setJobId] = useState("");

  const activeResumeId = resumeId || resumes.data?.[0]?.id || "";

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Workspace / ATS"
        title="Read the page like a machine."
        description="The saved resume is compiled, parsed, and scored. Add a job to check the match and the requirements it covers. Every run is stored on the resume."
        actions={
          activeResumeId ? (
            <Link to={`/app/resumes/${activeResumeId}/edit`}>
              <Button size="sm" variant="secondary">
                Open resume
              </Button>
            </Link>
          ) : null
        }
      />

      <div className="flex items-center gap-1 border-b border-line">
        {(
          [
            { id: "check", label: "Resume check", icon: Gauge },
            { id: "coverage", label: "Job coverage", icon: Target },
          ] as const
        ).map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => setTab(item.id)}
            className={cn(
              "flex items-center gap-1.5 border-b-2 px-3 py-2.5 text-[13px] transition-colors",
              tab === item.id ? "border-ink font-medium text-ink" : "border-transparent text-muted hover:text-ink",
            )}
          >
            <item.icon size={13} /> {item.label}
          </button>
        ))}
      </div>

      {resumes.isLoading ? (
        <Card className="p-8 text-sm text-muted">Loading resumes...</Card>
      ) : !resumes.data?.length ? (
        <EmptyState
          icon={<Gauge size={20} />}
          title="No resume to check"
          description="Create or import a resume first. The checker reads the compiled PDF, not the form fields."
          action={
            <Link to="/app/resumes?new=1">
              <Button size="sm">Create a resume</Button>
            </Link>
          }
        />
      ) : (
        <>
          <Card className="grid items-end gap-3 p-4 sm:grid-cols-2">
            <label className="min-w-0">
              <span className="mb-1 block font-mono text-[9px] uppercase tracking-[0.12em] text-muted">
                Resume
              </span>
              <select
                value={activeResumeId}
                onChange={(event) => setResumeId(event.target.value)}
                className="focus-ring h-10 w-full rounded-field border border-line bg-paper px-3 text-[13px]"
              >
                {resumes.data.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    {resume.title}
                    {resume.latestAts ? ` · last ${resume.latestAts.score}` : ""}
                  </option>
                ))}
              </select>
            </label>
            <label className="min-w-0">
              <span className="mb-1 block font-mono text-[9px] uppercase tracking-[0.12em] text-muted">
                Job post {tab === "coverage" ? "" : "(optional)"}
              </span>
              <select
                value={jobId}
                onChange={(event) => setJobId(event.target.value)}
                className="focus-ring h-10 w-full rounded-field border border-line bg-paper px-3 text-[13px]"
              >
                <option value="">{tab === "coverage" ? "Choose a saved job" : "No job, general check"}</option>
                {(jobs.data ?? []).map((job) => (
                  <option key={job.id} value={job.id}>
                    {[job.company, job.role].filter(Boolean).join(" · ") || "Saved posting"}
                  </option>
                ))}
              </select>
            </label>
          </Card>

          {tab === "check" ? (
            <ResumeCheck resumeId={activeResumeId} jobId={jobId} jobs={jobs.data ?? []} />
          ) : (
            <CoveragePanel resumeId={activeResumeId} jobId={jobId} />
          )}
        </>
      )}
    </div>
  );
}

function ErrorCard({ error }: { error: unknown }) {
  if (!error) return null;
  const quota = error instanceof ApiError && error.status === 402;
  return (
    <Card className="border-danger/20 bg-danger/5 p-4 text-sm text-danger">
      <p className="flex items-start gap-2">
        <AlertCircle size={15} className="mt-0.5 shrink-0" />
        {error instanceof Error ? error.message : "That did not work"}
      </p>
      {quota ? (
        <Link
          to="/app/billing"
          className="mt-2 inline-flex items-center gap-1 text-xs font-medium underline decoration-danger/30 underline-offset-2"
        >
          Compare plans <ArrowRight size={12} />
        </Link>
      ) : null}
    </Card>
  );
}

function ResumeCheck({ resumeId, jobId, jobs }: { resumeId: string; jobId: string; jobs: Job[] }) {
  const [report, setReport] = useState<AtsReportData | null>(null);
  const run = useMutation({
    mutationFn: () => api.atsReport(resumeId, jobId || undefined),
    onSuccess: (data) => setReport(data),
  });
  const job = jobs.find((item) => item.id === jobId);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-muted">
          {jobId
            ? `Includes the AI match against ${[job?.company, job?.role].filter(Boolean).join(" · ") || "the saved job"}.`
            : "Rule-based read only. Add a job for the keyword match."}
        </p>
        <Button onClick={() => run.mutate()} disabled={run.isPending || !resumeId}>
          <Gauge size={14} /> {run.isPending ? "Compiling and reading..." : "Run the check"}
        </Button>
      </div>

      <ErrorCard error={run.error} />

      {run.isPending ? (
        <Card className="p-8">
          <p className="font-display text-2xl">Reading the page</p>
          <p className="mt-1 max-w-xl text-sm leading-6 text-muted">
            The resume compiles, the text is extracted with its coordinates, and each check runs on what a
            parser can actually see.
          </p>
        </Card>
      ) : report ? (
        <Report report={report} />
      ) : (
        <Card className="p-8 text-sm text-muted">
          Run the check to see the score, every check with its fix, and the result stored on the resume.
        </Card>
      )}
    </div>
  );
}

function toneForGrade(grade: AtsReportData["grade"]) {
  return grade === "excellent" || grade === "good" ? "success" : grade === "fair" ? "warning" : "danger";
}

function Report({ report }: { report: AtsReportData }) {
  return (
    <div className="space-y-4">
      <Card className="p-5">
        <div className="flex flex-wrap items-end gap-5">
          <p className="font-display text-[72px] leading-none">{report.score}</p>
          <div className="min-w-0 flex-1 pb-1">
            <Badge tone={toneForGrade(report.grade) as "success" | "warning" | "danger"}>{report.grade}</Badge>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">{report.summary}</p>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-3 border-t border-line pt-4 sm:grid-cols-4">
          <Stat label="Words" value={report.stats.words} />
          <Stat label="Bullets" value={report.stats.bullets} />
          <Stat label="Quantified" value={report.stats.quantifiedBullets} />
          <Stat label="Parse rate" value={report.parse?.parseRate ? `${Math.round(report.parse.parseRate * 100)}%` : "—"} />
        </div>
      </Card>

      {report.title ? (
        <Card className="flex flex-wrap items-center justify-between gap-2 p-4">
          <div>
            <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">Title match</p>
            <p className="mt-1 text-sm">
              Job says <strong>{report.title.jobTitle}</strong>
              {report.title.best ? ` · your closest title is ${report.title.best}` : ""}
            </p>
          </div>
          <Badge tone={report.title.level === "exact" ? "success" : report.title.level === "close" ? "warning" : "danger"}>
            {report.title.level}
          </Badge>
        </Card>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        {report.categories.map((category) => (
          <CategoryCard key={category.id} category={category} />
        ))}
      </div>

      {report.keywords ? (
        <Card className="p-5">
          <div className="flex items-center justify-between">
            <p className="font-display text-xl">Keywords</p>
            <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-muted">
              {report.keywords.matched.length} matched · {report.keywords.missing.length} missing
            </span>
          </div>
          <div className="mt-4 grid gap-5 sm:grid-cols-2">
            <KeywordGroup label="Matched" items={report.keywords.matched} tone="success" />
            <KeywordGroup label="Missing" items={report.keywords.missing} tone="danger" />
            <KeywordGroup label="Hard skills missing" items={report.keywords.hard.missing} tone="warning" />
            <KeywordGroup label="Soft skills missing" items={report.keywords.soft.missing} tone="warning" />
          </div>
          {report.keywords.implied.length ? (
            <div className="mt-4 border-t border-line pt-3">
              <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">Implied by your experience</p>
              <ul className="mt-2 space-y-1 text-[12px] leading-5">
                {report.keywords.implied.map((item) => (
                  <li key={item.skill}>
                    <strong>{item.skill}</strong> <span className="text-muted">— {item.evidence}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </Card>
      ) : null}

      {report.knockouts?.length ? (
        <Card className="p-5">
          <p className="font-display text-xl">Knockout questions</p>
          <p className="mt-1 text-xs text-muted">A recruiter may screen on these before reading the resume.</p>
          <div className="mt-3 space-y-2">
            {report.knockouts.map((item) => (
              <div key={item.id} className="rounded-field border border-line bg-paper/40 p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge
                    tone={
                      item.status === "met"
                        ? "success"
                        : item.status === "not-met"
                          ? "danger"
                          : item.status === "unclear"
                            ? "warning"
                            : "outline"
                    }
                  >
                    {item.status}
                  </Badge>
                  <p className="text-[13px] font-medium">{item.label}</p>
                  {item.checkedWithAi ? <Badge tone="lime">AI checked</Badge> : null}
                </div>
                <p className="mt-1.5 text-[12px] leading-5 text-muted">{item.requirement}</p>
                <p className="mt-1 text-[12px] leading-5">{item.advice}</p>
              </div>
            ))}
          </div>
        </Card>
      ) : null}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">{label}</p>
      <p className="mt-1 font-display text-xl leading-none">{value}</p>
    </div>
  );
}

function CategoryCard({ category }: { category: AtsCategory }) {
  const ratio = category.maxScore ? category.score / category.maxScore : 0;
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <p className="font-display text-lg">{category.label}</p>
        <span className="font-mono text-[10px] text-muted">
          {category.score} / {category.maxScore}
        </span>
      </div>
      <div className="mt-2 h-1 overflow-hidden rounded-full bg-line">
        <div
          className={cn("h-full rounded-full", ratio >= 0.8 ? "bg-success" : ratio >= 0.5 ? "bg-warning" : "bg-danger")}
          style={{ width: `${Math.round(ratio * 100)}%` }}
        />
      </div>
      <div className="mt-3 space-y-2.5">
        {category.checks.map((check) => (
          <div key={check.id} className="border-t border-line pt-2.5 first:border-0 first:pt-0">
            <div className="flex items-start gap-2">
              {check.status === "pass" ? (
                <CheckCircle2 size={14} className="mt-0.5 shrink-0 text-success" />
              ) : check.status === "warn" ? (
                <AlertCircle size={14} className="mt-0.5 shrink-0 text-warning" />
              ) : (
                <XCircle size={14} className="mt-0.5 shrink-0 text-danger" />
              )}
              <div className="min-w-0">
                <p className="text-[13px] font-medium">{check.label}</p>
                <p className="mt-0.5 text-[12px] leading-5 text-muted">{check.detail}</p>
                {check.fix ? (
                  <p className="mt-1 text-[12px] leading-5">
                    <span className="font-mono text-[9px] uppercase tracking-[0.1em] text-muted">Fix · </span>
                    {check.fix}
                  </p>
                ) : null}
                {check.lines?.length ? (
                  <ul className="mt-1 space-y-0.5">
                    {check.lines.slice(0, 4).map((line, index) => (
                      <li key={index} className="truncate rounded bg-paper px-2 py-1 text-[11px] text-muted">
                        {line.text}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function KeywordGroup({
  label,
  items,
  tone,
}: {
  label: string;
  items: string[];
  tone: "success" | "danger" | "warning";
}) {
  if (!items.length) return null;
  return (
    <div>
      <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">{label}</p>
      <div className="mt-1.5 flex flex-wrap gap-1">
        {items.map((item) => (
          <Badge key={item} tone={tone}>
            {item}
          </Badge>
        ))}
      </div>
    </div>
  );
}

function CoveragePanel({ resumeId, jobId }: { resumeId: string; jobId: string }) {
  const run = useMutation({ mutationFn: () => api.coverage(resumeId, jobId) });
  const report = run.data;

  return (
    <div className="space-y-4">
      <Card className="flex flex-wrap items-center justify-between gap-3 p-4">
        <p className="max-w-xl text-xs leading-5 text-muted">
          Coverage checks each parsed requirement against the resume and your master profile. “In profile” means
          the fact exists and can be added without inventing anything.
        </p>
        <Button onClick={() => run.mutate()} disabled={!jobId || run.isPending}>
          <Target size={14} /> {run.isPending ? "Checking..." : "Check coverage"}
        </Button>
      </Card>

      <ErrorCard error={run.error} />

      {!jobId ? (
        <Card className="p-6 text-sm text-muted">Choose a saved job post to compare against.</Card>
      ) : report ? (
        <div className="space-y-4">
          <Card className="p-5">
            <div className="flex flex-wrap items-end gap-4">
              <p className="font-display text-6xl leading-none">
                {report.covered}
                <span className="text-muted">/{report.total}</span>
              </p>
              <div className="pb-1">
                <Badge tone={report.covered === report.total ? "success" : report.covered > report.total / 2 ? "warning" : "danger"}>
                  {report.total ? Math.round((report.covered / report.total) * 100) : 0}% covered
                </Badge>
                <p className="mt-1.5 text-xs text-muted">Must-have and nice-to-have requirements.</p>
              </div>
              {jobId ? (
                <Link to={`/app/resumes/${resumeId}/edit`} className="ml-auto">
                  <Button size="sm" variant="secondary">
                    Tailor this resume <ArrowRight size={13} />
                  </Button>
                </Link>
              ) : null}
            </div>
          </Card>

          <div className="grid gap-4 lg:grid-cols-3">
            <CoverageGroup title="Must have" checks={report.mustHave} />
            <CoverageGroup title="Nice to have" checks={report.niceToHave} />
            <CoverageGroup title="Keywords" checks={report.keywords} />
          </div>
        </div>
      ) : (
        <Card className="flex items-center gap-2 p-6 text-sm text-muted">
          <ListChecks size={15} /> Nothing compared yet.
        </Card>
      )}
    </div>
  );
}

function CoverageGroup({ title, checks }: { title: string; checks: CoverageCheck[] }) {
  return (
    <Card className="p-4">
      <p className="font-display text-lg">{title}</p>
      {!checks.length ? (
        <p className="mt-2 text-xs text-muted">Not extracted from this job.</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {checks.map((check) => (
            <li key={check.requirement} className="flex items-start gap-2 text-[12px] leading-5">
              {check.status === "covered" ? (
                <CheckCircle2 size={13} className="mt-1 shrink-0 text-success" />
              ) : check.status === "in_profile" ? (
                <Circle size={13} className="mt-1 shrink-0 text-warning" />
              ) : (
                <XCircle size={13} className="mt-1 shrink-0 text-danger" />
              )}
              <span className="min-w-0">
                <span className={cn(check.status === "missing" && "text-muted line-through decoration-danger/40")}>
                  {check.requirement}
                </span>
                {check.status === "in_profile" ? (
                  <span className="ml-1.5 font-mono text-[9px] uppercase tracking-[0.08em] text-warning">in profile</span>
                ) : null}
                {check.foundIn.length ? (
                  <span className="ml-1.5 text-[10px] text-muted">{check.foundIn.slice(0, 2).join(", ")}</span>
                ) : null}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
