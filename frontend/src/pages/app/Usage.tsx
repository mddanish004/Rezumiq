import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ArrowUpRight, Sparkles } from "lucide-react";
import { api, type AiRuns, type Usage as UsageType } from "@/lib/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatDate, formatRelative, usdFromMicros } from "@/lib/utils";

const planName: Record<string, string> = { free: "Free tier", season_pass: "Season Pass", pro: "Pro" };

export default function Usage() {
  const usage = useQuery<UsageType>({ queryKey: ["usage"], queryFn: api.usage });
  const runs = useQuery<AiRuns>({ queryKey: ["ai-runs"], queryFn: api.aiRuns });

  if (usage.isLoading) {
    return <p className="text-sm text-muted">Loading usage...</p>;
  }
  if (!usage.data) {
    return <p className="text-sm text-danger">Could not load usage.</p>;
  }
  const data = usage.data;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Preferences / Usage"
        title="What the plan has used."
        description={`This period runs ${formatDate(data.periodStart)} to ${formatDate(data.periodEnd)}. Limits reset on the first of next month, in UTC.`}
        actions={
          <Link to="/app/billing" className="text-sm font-medium underline decoration-line underline-offset-4 hover:decoration-ink">
            Manage plan
          </Link>
        }
      />

      <div className="grid gap-4 lg:grid-cols-[0.7fr_1.3fr]">
        <Card className="p-5">
          <p className="eyebrow">Current plan</p>
          <p className="mt-2 font-display text-2xl">{planName[data.plan]}</p>
          <p className="mt-1 text-xs text-muted">
            {data.ownAiKey ? "Your own AI key is connected." : "Requests use the Rezumiq AI key."}
          </p>
          <div className="mt-4 space-y-2 border-t border-line pt-4 text-sm">
            <div className="flex justify-between"><span className="text-muted">Resumes</span><span>{data.resumes.used} / ∞</span></div>
            <div className="flex justify-between"><span className="text-muted">AI tailors</span><span>{data.tailor.used} / {data.tailor.limit}</span></div>
            <div className="flex justify-between"><span className="text-muted">AI edits</span><span>{data.edit.used} / {data.edit.limit}</span></div>
            <div className="flex justify-between"><span className="text-muted">Imports</span><span>{data.import.used} / {data.import.limit}</span></div>
            <div className="flex justify-between"><span className="text-muted">AI drafts</span><span>{data.draft.used} / {data.draft.limit}{data.plan === "free" ? " (all time)" : ""}</span></div>
            <div className="flex justify-between"><span className="text-muted">Job parses</span><span>{data.job.used} / {data.job.limit}</span></div>
            <div className="flex justify-between"><span className="text-muted">ATS checks</span><span>{data.ats.used} / {data.ats.limit}</span></div>
            <div className="flex justify-between"><span className="text-muted">AI reviews</span><span>{data.review.used} / {data.review.limit}</span></div>
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow">AI runs</p>
              <p className="mt-2 font-display text-2xl">{runs.data?.runs.length ?? 0} recent runs</p>
              <p className="mt-1 text-xs text-muted">
                Only usage numbers are kept: no prompts, outputs, errors, or resume content.
              </p>
            </div>
            <Badge tone="lime"><Sparkles size={10} /> {usdFromMicros(runs.data?.monthCostUsdMicros ?? 0)} this month</Badge>
          </div>
          <div className="mt-4 overflow-x-auto">
            {runs.data?.runs.length ? (
              <table className="w-full min-w-[640px] border-collapse text-left text-xs">
                <thead>
                  <tr className="border-b border-line font-mono text-[9px] uppercase tracking-[0.1em] text-muted">
                    <th className="py-2 pr-4 font-normal">When</th>
                    <th className="py-2 pr-4 font-normal">Step</th>
                    <th className="py-2 pr-4 font-normal">Status</th>
                    <th className="py-2 pr-4 font-normal">Model</th>
                    <th className="py-2 pr-4 text-right font-normal">Tokens</th>
                    <th className="py-2 pr-4 text-right font-normal">Cost</th>
                    <th className="py-2 text-right font-normal">Latency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line/70">
                  {runs.data.runs.map((run) => (
                    <tr key={run.id}>
                      <td className="py-2.5 pr-4 text-muted">{formatRelative(run.createdAt)}</td>
                      <td className="py-2.5 pr-4 font-mono text-[10px] uppercase tracking-[0.08em]">{run.step}</td>
                      <td className="py-2.5 pr-4">
                        <Badge tone={run.status === "succeeded" ? "success" : run.status === "failed" ? "danger" : "outline"}>
                          {run.status}
                        </Badge>
                      </td>
                      <td className="max-w-40 truncate py-2.5 pr-4 text-muted">{run.model || "pending"}</td>
                      <td className="py-2.5 pr-4 text-right text-muted">{run.inputTokens + run.outputTokens}</td>
                      <td className="py-2.5 pr-4 text-right text-muted">
                        {run.costUsdMicros === null ? "Unpriced" : usdFromMicros(run.costUsdMicros)}
                      </td>
                      <td className="py-2.5 text-right text-muted">{run.latencyMs ? `${run.latencyMs}ms` : "n/a"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <EmptyState
                icon={<Sparkles size={20} />}
                title="No AI runs yet"
                description="Imports, drafts, tailoring, and reviews appear here once you use them."
                action={
                  <Link to="/app/resumes" className="inline-flex items-center gap-1 text-sm font-medium">
                    Start a resume <ArrowUpRight size={13} />
                  </Link>
                }
              />
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
