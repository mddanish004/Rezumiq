import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { BarChart3, ExternalLink, Globe2, Link2, MonitorSmartphone, MousePointerClick } from "lucide-react";
import { api, type Analytics } from "@/lib/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Spinner } from "@/components/ui/Spinner";
import { cn, formatRelative } from "@/lib/utils";

const ranges = [7, 30, 90] as const;

export default function AnalyticsPage() {
  const [days, setDays] = useState<number>(30);
  const analytics = useQuery<Analytics>({
    queryKey: ["analytics", days],
    queryFn: () => api.analytics(days),
  });

  const data = analytics.data;
  const hasViews = Boolean(data?.totals.views);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Workspace / Analytics"
        title="What happens after you share."
        description="Views on public links, where they came from, and the device they opened on. Your own visits are not counted."
        actions={
          <div className="flex gap-1 rounded-field border border-line bg-surface p-1">
            {ranges.map((range) => (
              <button
                key={range}
                type="button"
                onClick={() => setDays(range)}
                className={cn(
                  "rounded px-2.5 py-1.5 text-[12px] transition-colors",
                  days === range ? "bg-ink text-paper" : "text-muted hover:text-ink",
                )}
              >
                {range}d
              </button>
            ))}
          </div>
        }
      />

      {analytics.isLoading ? (
        <div className="grid place-items-center py-24">
          <Spinner label="Reading link views" />
        </div>
      ) : analytics.isError ? (
        <Card className="p-6 text-sm text-danger">Analytics could not be loaded.</Card>
      ) : !hasViews ? (
        <EmptyState
          icon={<BarChart3 size={20} />}
          title="No views yet"
          description="Create a share link and send it somewhere. Views, sources, and devices appear here within a minute of the first open."
          action={
            <Link to="/app/resumes">
              <Button size="sm">Create a share link</Button>
            </Link>
          }
        />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Metric
              label="Views"
              value={data!.totals.views}
              delta={delta(data!.totals.views, data!.totals.previousViews)}
              hint={`${data!.totals.previousViews} in the previous ${days} days`}
            />
            <Metric
              label="Unique visitors"
              value={data!.totals.uniqueVisitors}
              delta={delta(data!.totals.uniqueVisitors, data!.totals.previousUniqueVisitors)}
              hint={`${data!.totals.previousUniqueVisitors} previously`}
            />
            <Metric label="Live links" value={data!.links.length} hint="Unrevoked public links" />
            <Metric
              label="Last open"
              value={data!.recentViews[0] ? formatRelative(data!.recentViews[0].viewedAt) : "—"}
              hint={data!.recentViews[0]?.resumeTitle ?? "No recent view"}
            />
          </div>

          <Card className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-display text-xl">Views over time</p>
                <p className="mt-0.5 text-xs text-muted">Daily opens in your time zone.</p>
              </div>
              <Badge>{days} days</Badge>
            </div>
            <div className="mt-4 h-[240px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data!.viewsByDay} margin={{ top: 4, right: 8, left: -22, bottom: 0 }}>
                  <defs>
                    <linearGradient id="viewsFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#1F5A46" stopOpacity={0.22} />
                      <stop offset="100%" stopColor="#1F5A46" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#E3DFD6" strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="day"
                    tick={{ fontSize: 10, fill: "#66645E" }}
                    tickLine={false}
                    axisLine={false}
                    minTickGap={28}
                    tickFormatter={(value: string) => value.slice(5)}
                  />
                  <YAxis
                    allowDecimals={false}
                    tick={{ fontSize: 10, fill: "#66645E" }}
                    tickLine={false}
                    axisLine={false}
                    width={40}
                  />
                  <Tooltip
                    contentStyle={{
                      borderRadius: 8,
                      border: "1px solid #E3DFD6",
                      fontSize: 12,
                      boxShadow: "0 8px 24px rgba(20,20,20,0.08)",
                    }}
                    labelStyle={{ color: "#66645E", fontSize: 10 }}
                  />
                  <Area
                    type="monotone"
                    dataKey="views"
                    stroke="#1F5A46"
                    strokeWidth={1.5}
                    fill="url(#viewsFill)"
                    name="Views"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <div className="grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
            <Card className="p-5">
              <p className="font-display text-xl">Links</p>
              <div className="mt-3 divide-y divide-line">
                {data!.links.map((link) => (
                  <div key={link.id} className="flex items-center gap-3 py-2.5">
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-field border border-line bg-paper">
                      <Link2 size={13} />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[13px] font-medium">{link.resumeTitle || link.slug}</p>
                      <p className="truncate font-mono text-[10px] text-muted">/{link.slug}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-mono text-[12px]">{link.views}</p>
                      <p className="font-mono text-[9px] uppercase tracking-[0.08em] text-muted">
                        {link.totalViews} total
                      </p>
                    </div>
                  </div>
                ))}
              </div>
              <Link to="/app/resumes" className="mt-3 inline-flex items-center gap-1 text-[12px] text-muted hover:text-ink">
                Manage links on resumes <ExternalLink size={11} />
              </Link>
            </Card>

            <Card className="p-5">
              <p className="font-display text-xl">Sources</p>
              <Breakdown icon={<MousePointerClick size={13} />} items={data!.referrers} empty="All opens were direct." />
              <div className="mt-5 border-t border-line pt-4">
                <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">Countries</p>
                <Breakdown icon={<Globe2 size={13} />} items={data!.countries} empty="No location data yet." compact />
              </div>
              <div className="mt-5 border-t border-line pt-4">
                <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">Devices</p>
                <Breakdown icon={<MonitorSmartphone size={13} />} items={data!.devices} empty="No device data yet." compact />
              </div>
            </Card>
          </div>

          <Card className="p-5">
            <p className="font-display text-xl">Recent opens</p>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full min-w-[560px] text-left text-[12px]">
                <thead>
                  <tr className="border-b border-line font-mono text-[9px] uppercase tracking-[0.1em] text-muted">
                    <th className="pb-2 font-normal">Resume</th>
                    <th className="pb-2 font-normal">Source</th>
                    <th className="pb-2 font-normal">Place</th>
                    <th className="pb-2 font-normal">Device</th>
                    <th className="pb-2 text-right font-normal">When</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {data!.recentViews.map((view) => (
                    <tr key={view.id}>
                      <td className="max-w-[220px] truncate py-2">{view.resumeTitle || view.slug}</td>
                      <td className="py-2 text-muted">{view.referrer || "direct"}</td>
                      <td className="py-2 text-muted">{view.country || "—"}</td>
                      <td className="py-2 text-muted">{view.device || "—"}</td>
                      <td className="py-2 text-right font-mono text-[10px] text-muted">
                        {formatRelative(view.viewedAt)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

function Metric({
  label,
  value,
  delta,
  hint,
}: {
  label: string;
  value: number | string;
  delta?: number | null;
  hint: string;
}) {
  return (
    <Card className="p-4">
      <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">{label}</p>
      <div className="mt-1 flex items-baseline gap-2">
        <p className="font-display text-3xl leading-none">{value}</p>
        {delta !== undefined && delta !== null && Number.isFinite(delta) ? (
          <span className={cn("font-mono text-[10px]", delta >= 0 ? "text-success" : "text-danger")}>
            {delta >= 0 ? "+" : ""}
            {delta}%
          </span>
        ) : null}
      </div>
      <p className="mt-1.5 truncate text-[11px] text-muted">{hint}</p>
    </Card>
  );
}

function delta(now: number, before: number) {
  if (!before) return now ? 100 : 0;
  return Math.round(((now - before) / before) * 100);
}

function Breakdown({
  icon,
  items,
  empty,
  compact = false,
}: {
  icon: ReactNode;
  items: Array<{ label: string; views: number }>;
  empty: string;
  compact?: boolean;
}) {
  const max = Math.max(1, ...items.map((item) => item.views));
  if (!items.length) return <p className="mt-2 text-[12px] text-muted">{empty}</p>;
  return (
    <div className={cn("space-y-2", compact ? "mt-2" : "mt-3")}>
      {items.map((item) => (
        <div key={item.label}>
          <div className="flex items-center justify-between text-[12px]">
            <span className="flex min-w-0 items-center gap-1.5 truncate text-muted">
              {icon} {item.label}
            </span>
            <span className="font-mono text-[11px]">{item.views}</span>
          </div>
          <div className="mt-1 h-[3px] overflow-hidden rounded-full bg-line">
            <div className="h-full rounded-full bg-forest/60" style={{ width: `${(item.views / max) * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function Badge({ children }: { children: ReactNode }) {
  return (
    <span className="rounded-full border border-line bg-paper px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.1em] text-muted">
      {children}
    </span>
  );
}
