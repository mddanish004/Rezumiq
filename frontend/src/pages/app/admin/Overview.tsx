import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, type AdminOverview } from "@/lib/api";
import { Spinner } from "@/components/ui/Spinner";
import { formatRelative, inr, usdFromMicros } from "@/lib/utils";
import {
  AdminMetric,
  BreakdownList,
  Funnel,
  Panel,
  RangeTabs,
  axisStyle,
  delta,
  formatNumber,
  tooltipStyle,
} from "./shared";

export function AdminOverviewTab() {
  const [days, setDays] = useState(30);
  const overview = useQuery<AdminOverview>({
    queryKey: ["admin-overview", days],
    queryFn: () => api.adminOverview(days),
  });

  if (overview.isLoading || !overview.data) {
    return (
      <div className="grid place-items-center py-20">
        <Spinner label="Reading the control room" />
      </div>
    );
  }
  if (overview.isError) {
    return <p className="text-sm text-danger">The overview could not be loaded.</p>;
  }

  const data = overview.data;
  const totals = data.totals;
  const active = data.byDay.some((day) => day.signups || day.resumes || day.aiRuns || day.views);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-muted">Compared with the previous {days} days.</p>
        <RangeTabs days={days} onChange={setDays} />
      </div>

      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <AdminMetric
          label="Users"
          value={formatNumber(totals.users)}
          hint={`${totals.guests} guests · ${totals.suspendedUsers} suspended`}
        />
        <AdminMetric
          label="New users"
          value={formatNumber(totals.newUsers)}
          delta={delta(totals.newUsers, totals.previousNewUsers)}
          hint={`${totals.previousNewUsers} in the previous period`}
        />
        <AdminMetric
          label="Active users"
          value={formatNumber(totals.activeUsers)}
          delta={delta(totals.activeUsers, totals.previousActiveUsers)}
          hint="Opened the workspace"
        />
        <AdminMetric label="Paid users" value={formatNumber(totals.paidUsers)} hint="Season Pass or Pro" />
        <AdminMetric
          label="Resumes created"
          value={formatNumber(totals.resumesCreated)}
          delta={delta(totals.resumesCreated, totals.previousResumesCreated)}
          hint={`${formatNumber(totals.resumes)} live in total`}
        />
        <AdminMetric
          label="AI runs"
          value={formatNumber(totals.aiRuns)}
          delta={delta(totals.aiRuns, totals.previousAiRuns)}
          hint={`${usdFromMicros(totals.aiCostUsdMicros)} · ${totals.aiFailed} failed`}
        />
        <AdminMetric
          label="Revenue"
          value={inr(totals.revenuePaise)}
          delta={delta(totals.revenuePaise, totals.previousRevenuePaise)}
          hint={`${inr(totals.previousRevenuePaise)} previously`}
        />
        <AdminMetric
          label="Share views"
          value={formatNumber(totals.shareViews)}
          delta={delta(totals.shareViews, totals.previousShareViews)}
          hint={`${formatNumber(totals.previousShareViews)} previously`}
        />
      </div>

      <Panel
        title="Activity"
        description="Signups, resumes, AI calls, and public link views per day."
        action={!active ? <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-muted">Quiet period</span> : null}
      >
        <div className="h-[260px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data.byDay} margin={{ top: 4, right: 8, left: -22, bottom: 0 }}>
              <defs>
                <linearGradient id="signupFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#141414" stopOpacity={0.14} />
                  <stop offset="100%" stopColor="#141414" stopOpacity={0} />
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
              <Legend wrapperStyle={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.08em" }} />
              <Area type="monotone" dataKey="signups" name="Signups" stroke="#141414" strokeWidth={1.5} fill="url(#signupFill)" />
              <Line type="monotone" dataKey="resumes" name="Resumes" stroke="#1F5A46" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="aiRuns" name="AI runs" stroke="#A66A12" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="views" name="Views" stroke="#66645E" strokeWidth={1.2} strokeDasharray="4 3" dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="Funnel" description="How far the last cohort gets.">
          <Funnel
            steps={[
              { label: "Signed up", value: data.funnel.signedUp },
              { label: "Made a resume", value: data.funnel.createdResume },
              { label: "Used AI", value: data.funnel.usedAi },
              { label: "Shared", value: data.funnel.shared },
              { label: "Paid", value: data.funnel.paid },
            ]}
          />
        </Panel>
        <Panel title="Plans" description="Current accounts by plan.">
          <BreakdownList items={data.plans} />
        </Panel>
        <Panel title="Sign-in providers" description="Accounts linked to a provider.">
          <BreakdownList items={data.providers} empty="Everyone signs in with a password." />
        </Panel>
      </div>

      <Panel
        title="Recent signups"
        description="The newest accounts, newest first."
        action={
          <span className="font-mono text-[9px] uppercase tracking-[0.1em] text-muted">{data.recentSignups.length} shown</span>
        }
      >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-left text-[12px] [&_td]:pr-3 [&_th]:pr-3">
            <thead>
              <tr className="border-b border-line font-mono text-[9px] uppercase tracking-[0.1em] text-muted">
                <th className="pb-2 font-normal">Person</th>
                <th className="pb-2 font-normal">Plan</th>
                <th className="pb-2 font-normal">Providers</th>
                <th className="pb-2 text-right font-normal">Joined</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {data.recentSignups.map((signup) => (
                <tr key={signup.id}>
                  <td className="py-2.5">
                    <p className="font-medium">{signup.name || "No name"}</p>
                    <p className="font-mono text-[10px] text-muted">{signup.email}</p>
                  </td>
                  <td className="py-2.5 capitalize text-muted">{signup.plan.replace("_", " ")}</td>
                  <td className="py-2.5 text-muted">{signup.providers.join(", ") || "password"}</td>
                  <td className="py-2.5 text-right font-mono text-[10px] text-muted">
                    {formatRelative(signup.createdAt)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Link to="/app/admin?tab=users" className="mt-3 inline-flex text-[12px] text-muted hover:text-ink">
          Open the user list
        </Link>
      </Panel>
    </div>
  );
}
