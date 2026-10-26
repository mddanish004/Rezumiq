import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, type AdminAi } from "@/lib/api";
import { Spinner } from "@/components/ui/Spinner";
import { formatRelative, usdFromMicros } from "@/lib/utils";
import {
  AdminMetric,
  BreakdownList,
  EmptyRow,
  Panel,
  RangeTabs,
  axisStyle,
  formatNumber,
  tooltipStyle,
} from "./shared";

export function AdminAiTab() {
  const [days, setDays] = useState(30);
  const ai = useQuery<AdminAi>({ queryKey: ["admin-ai", days], queryFn: () => api.adminAi(days) });

  if (ai.isLoading || !ai.data) {
    return (
      <div className="grid place-items-center py-20">
        <Spinner label="Reading AI usage" />
      </div>
    );
  }
  if (ai.isError) return <p className="text-sm text-danger">AI usage could not be loaded.</p>;

  const data = ai.data;
  const totals = data.totals;
  const tokens = totals.inputTokens + totals.outputTokens;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-muted">Cost includes cached input where the provider reports it.</p>
        <RangeTabs days={days} onChange={setDays} />
      </div>

      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <AdminMetric label="Runs" value={formatNumber(totals.runs)} hint={`${totals.users} people used AI`} />
        <AdminMetric label="Failed" value={formatNumber(totals.failed)} hint={`${totals.byok} ran on a personal key`} />
        <AdminMetric label="Cost" value={usdFromMicros(totals.costUsdMicros)} hint={`${formatNumber(tokens)} tokens`} />
        <AdminMetric
          label="Cached input"
          value={formatNumber(totals.cachedInputTokens)}
          hint={`${formatNumber(totals.inputTokens)} fresh input tokens`}
        />
      </div>

      <Panel title="Runs over time" description="One point per day in your time zone.">
        <div className="h-[220px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.byDay} margin={{ top: 4, right: 8, left: -22, bottom: 0 }}>
              <defs>
                <linearGradient id="aiFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#1F5A46" stopOpacity={0.2} />
                  <stop offset="100%" stopColor="#1F5A46" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#E3DFD6" strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="day"
                tick={axisStyle}
                tickLine={false}
                axisLine={false}
                minTickGap={28}
                tickFormatter={(value: string) => value.slice(5)}
              />
              <YAxis allowDecimals={false} tick={axisStyle} tickLine={false} axisLine={false} width={40} />
              <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: "#66645E", fontSize: 10 }} />
              <Area type="monotone" dataKey="runs" name="Runs" stroke="#1F5A46" strokeWidth={1.5} fill="url(#aiFill)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
        <Panel title="By step" description="Where the tokens go, with latency percentiles.">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[460px] text-left text-[12px] [&_td]:pr-3 [&_th]:pr-3">
              <thead>
                <tr className="border-b border-line font-mono text-[9px] uppercase tracking-[0.1em] text-muted">
                  <th className="pb-2 font-normal">Step</th>
                  <th className="pb-2 text-right font-normal">Runs</th>
                  <th className="pb-2 text-right font-normal">Failed</th>
                  <th className="pb-2 text-right font-normal">p50</th>
                  <th className="pb-2 text-right font-normal">p95</th>
                  <th className="pb-2 text-right font-normal">Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {data.bySteps.length ? (
                  data.bySteps.map((step) => (
                    <tr key={step.step}>
                      <td className="py-2 font-mono text-[11px]">{step.step}</td>
                      <td className="py-2 text-right font-mono">{step.runs}</td>
                      <td className="py-2 text-right font-mono">{step.failed}</td>
                      <td className="py-2 text-right font-mono text-[11px] text-muted">
                        {step.p50Ms ? `${step.p50Ms}ms` : "—"}
                      </td>
                      <td className="py-2 text-right font-mono text-[11px] text-muted">
                        {step.p95Ms ? `${step.p95Ms}ms` : "—"}
                      </td>
                      <td className="py-2 text-right font-mono text-[11px]">{usdFromMicros(step.costUsdMicros)}</td>
                    </tr>
                  ))
                ) : (
                  <EmptyRow colSpan={6}>No AI runs in this period.</EmptyRow>
                )}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="By model" description="Which model served the calls.">
          <div className="space-y-3">
            {data.byModels.length ? (
              data.byModels.map((model) => (
                <div key={model.model} className="rounded-field border border-line bg-paper/40 p-3">
                  <p className="truncate font-mono text-[11px]">{model.model}</p>
                  <div className="mt-1 flex items-center justify-between text-[11px] text-muted">
                    <span>{formatNumber(model.runs)} runs</span>
                    <span>{formatNumber(model.tokens)} tokens</span>
                    <span>{usdFromMicros(model.costUsdMicros)}</span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-[12px] text-muted">No model calls yet.</p>
            )}
          </div>
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Top users" description="By spend in this period.">
          <BreakdownList
            items={data.topUsers.map((user) => ({
              key: String(user.userId),
              label: user.name || user.email,
              count: user.costUsdMicros,
            }))}
            empty="Nobody has used AI yet."
            formatValue={usdFromMicros}
          />
        </Panel>
        <Panel title="Failures" description="The last failed calls, newest first.">
          {data.failures.length ? (
            <div className="space-y-2">
              {data.failures.map((failure) => (
                <div key={failure.id} className="rounded-field border border-danger/15 bg-danger/5 p-2.5">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-mono text-[10px] uppercase tracking-[0.08em] text-danger">
                      {failure.step} · {failure.model}
                    </p>
                    <span className="font-mono text-[9px] text-muted">{formatRelative(failure.createdAt)}</span>
                  </div>
                  <p className="mt-1 truncate text-[11px]">{failure.error || "Unknown error"}</p>
                  <p className="mt-0.5 truncate font-mono text-[9px] text-muted">{failure.email}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-[12px] text-muted">No failures in this period.</p>
          )}
        </Panel>
      </div>
    </div>
  );
}
