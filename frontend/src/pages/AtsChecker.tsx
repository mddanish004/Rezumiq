import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Check, Gauge, Sparkles, TriangleAlert } from "lucide-react";
import { api, type AtsReportData } from "@/lib/api";
import { PublicHeader } from "@/components/public/PublicHeader";
import { PublicFooter } from "@/components/public/PublicFooter";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";

const GRADE_COPY: Record<string, string> = {
  excellent: "Excellent",
  good: "Good",
  fair: "Fair",
  poor: "Needs work",
};

export default function AtsChecker() {
  const [text, setText] = useState("");
  const [job, setJob] = useState("");
  const [report, setReport] = useState<AtsReportData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const check = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    if (text.trim().length < 200) {
      setError("Paste at least 200 characters. The rule engine needs enough resume to read.");
      return;
    }
    setLoading(true);
    try {
      const data = await api.publicAts(text.trim(), job.trim() || undefined);
      setReport(data);
      window.setTimeout(() => {
        document.getElementById("ats-report")?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 50);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not run the check. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-paper">
      <PublicHeader />
      <main>
        <section className="border-b border-line">
          <div className="mx-auto grid max-w-[1240px] gap-10 px-5 py-14 lg:grid-cols-[0.9fr_1.1fr] lg:px-8 lg:py-20">
            <div>
              <Badge tone="lime" className="px-3 py-1 text-[9px]">
                Free ATS checker
              </Badge>
              <h1 className="mt-5 font-display text-4xl leading-[1.02] tracking-[-0.03em] sm:text-5xl">
                See what the parser
                <br />
                <span className="italic text-muted">actually sees.</span>
              </h1>
              <p className="mt-5 max-w-lg text-sm leading-7 text-muted">
                Paste your resume text and, if you have one, the job description. The rule engine scores
                parsing, contact details, sections, impact, length, and job match. No account needed.
              </p>
              <ul className="mt-6 space-y-2.5">
                {[
                  "Every warning names the line and a fix",
                  "Keyword match and knockout requirements",
                  "AI matching adds a second reading when you sign in",
                ].map((item) => (
                  <li key={item} className="flex items-center gap-2.5 text-sm text-muted">
                    <span className="grid h-5 w-5 place-items-center rounded-full border border-line bg-surface">
                      <Check size={11} className="text-forest" strokeWidth={3} />
                    </span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <Card className="p-5 sm:p-6">
              <form onSubmit={check} className="space-y-4">
                <label className="block">
                  <span className="mb-1.5 flex items-center justify-between font-mono text-[10px] uppercase tracking-[0.16em] text-muted">
                    Resume text
                    <span className="normal-case tracking-normal">{text.length} chars</span>
                  </span>
                  <textarea
                    value={text}
                    onChange={(event) => setText(event.target.value)}
                    rows={8}
                    placeholder="Paste the resume text, exactly as a recruiter would receive it."
                    className="focus-ring w-full resize-y rounded-field border border-line bg-paper p-3 text-sm leading-6 placeholder:text-muted/60"
                  />
                </label>
                <label className="block">
                  <span className="mb-1.5 block font-mono text-[10px] uppercase tracking-[0.16em] text-muted">
                    Job description <span className="normal-case tracking-normal">(optional)</span>
                  </span>
                  <textarea
                    value={job}
                    onChange={(event) => setJob(event.target.value)}
                    rows={4}
                    placeholder="Paste the posting to unlock keyword match, title match, and knockouts."
                    className="focus-ring w-full resize-y rounded-field border border-line bg-paper p-3 text-sm leading-6 placeholder:text-muted/60"
                  />
                </label>
                {error ? (
                  <p role="alert" className="rounded-field border border-danger/20 bg-danger/5 px-3 py-2.5 text-sm text-danger">
                    {error}
                  </p>
                ) : null}
                <Button type="submit" className="w-full" size="lg" disabled={loading}>
                  {loading ? "Reading the resume..." : "Run the ATS report"}
                  {!loading ? <ArrowRight size={15} /> : null}
                </Button>
                <p className="text-center text-[11px] text-muted">
                  Nothing is stored. Public checks are scored in memory.
                </p>
              </form>
            </Card>
          </div>
        </section>

        {report ? <Report report={report} /> : null}
      </main>
      <PublicFooter />
    </div>
  );
}

function Report({ report }: { report: AtsReportData }) {
  const grade = GRADE_COPY[report.grade] ?? report.grade;
  return (
    <section id="ats-report" className="mx-auto max-w-[1240px] px-5 py-14 lg:px-8 lg:py-20">
      <div className="grid gap-4 lg:grid-cols-[0.75fr_1.25fr]">
        <Card className="flex flex-col items-start p-6">
          <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted">ATS score</p>
          <div className="mt-4 flex items-end gap-3">
            <span className="font-display text-7xl leading-none tracking-[-0.04em]">{report.score}</span>
            <span className="pb-2 font-mono text-[10px] uppercase tracking-[0.12em] text-muted">/ 100</span>
          </div>
          <Badge tone={report.grade === "excellent" ? "success" : report.grade === "good" ? "lime" : "warning"} className="mt-4">
            {grade}
          </Badge>
          <p className="mt-4 text-sm leading-6 text-muted">{report.summary}</p>
          <div className="mt-6 grid w-full grid-cols-2 gap-3 border-t border-line pt-4 text-sm">
            <Stat label="Words" value={report.stats.words} />
            <Stat label="Bullets" value={report.stats.bullets} />
            <Stat label="Sections" value={report.stats.sections.length} />
            <Stat label="Quantified bullets" value={report.stats.quantifiedBullets} />
          </div>
          {report.title ? (
            <p className="mt-4 w-full rounded-field border border-line bg-paper px-3 py-2 text-xs text-muted">
              Closest title: <span className="text-ink">{report.title.best ?? "None"}</span> for{" "}
              <span className="text-ink">{report.title.jobTitle}</span> ({report.title.level})
            </p>
          ) : null}
          <Link to="/signup" className="mt-5 w-full">
            <Button className="w-full">
              <Sparkles size={14} /> Add AI matching
            </Button>
          </Link>
          <p className="mt-2 text-[11px] leading-5 text-muted">
            AI matching runs on a signed-in account. The AI review needs Season Pass or Pro.
          </p>
        </Card>

        <div className="space-y-4">
          {report.categories.map((category) => (
            <Card key={category.id} className="p-5">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Gauge size={15} className="text-muted" />
                  <p className="text-sm font-medium">{category.label}</p>
                </div>
                <span className="font-mono text-[11px] text-muted">
                  {category.score} / {category.maxScore}
                </span>
              </div>
              <div className="mt-3 space-y-2.5">
                {category.checks.map((item) => (
                  <div key={item.id} className="flex gap-2.5 border-t border-line/70 pt-2.5 first:border-0 first:pt-0">
                    <span
                      className={`mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded-full ${
                        item.status === "pass"
                          ? "bg-forest/10 text-forest"
                          : item.status === "warn"
                            ? "bg-warning/10 text-warning"
                            : "bg-danger/10 text-danger"
                      }`}
                    >
                      {item.status === "pass" ? <Check size={10} strokeWidth={3} /> : <TriangleAlert size={10} />}
                    </span>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-baseline gap-x-2">
                        <p className="text-[13px] font-medium">{item.label}</p>
                        <p className="text-[11px] text-muted">{item.detail}</p>
                      </div>
                      {item.fix ? <p className="mt-0.5 text-[12px] leading-5 text-muted">{item.fix}</p> : null}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      </div>

      {report.keywords ? (
        <Card className="mt-4 p-5">
          <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted">Keywords</p>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {report.keywords.matched.map((skill) => (
              <Badge key={`m-${skill}`} tone="success">{skill}</Badge>
            ))}
            {report.keywords.missing.map((skill) => (
              <Badge key={`x-${skill}`} tone="danger">{skill}</Badge>
            ))}
            {report.keywords.implied.map((item) => (
              <Badge key={`i-${item.skill}`} tone="lime">{item.skill} · implied</Badge>
            ))}
          </div>
          {report.keywords.mustHaveMissing.length ? (
            <p className="mt-3 text-xs text-muted">
              Must-have skills missing: {report.keywords.mustHaveMissing.join(", ")}
            </p>
          ) : null}
        </Card>
      ) : null}

      {report.knockouts?.length ? (
        <Card className="mt-4 p-5">
          <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted">Knockout requirements</p>
          <div className="mt-3 divide-y divide-line">
            {report.knockouts.map((knockout) => (
              <div key={knockout.id} className="flex flex-wrap items-start justify-between gap-2 py-3 first:pt-0 last:pb-0">
                <div>
                  <p className="text-[13px] font-medium">{knockout.label}</p>
                  <p className="text-xs text-muted">{knockout.requirement}</p>
                  {knockout.evidence ? <p className="mt-1 text-xs text-forest">Evidence: {knockout.evidence}</p> : null}
                </div>
                <div className="flex items-center gap-1.5">
                  <Badge tone={knockout.status === "met" ? "success" : knockout.status === "unclear" ? "warning" : "danger"}>
                    {knockout.status}
                  </Badge>
                  {knockout.checkedWithAi ? <Badge tone="lime">AI checked</Badge> : null}
                </div>
              </div>
            ))}
          </div>
        </Card>
      ) : null}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <p className="font-mono text-[9px] uppercase tracking-[0.1em] text-muted">{label}</p>
      <p className="mt-1 text-lg">{value}</p>
    </div>
  );
}
