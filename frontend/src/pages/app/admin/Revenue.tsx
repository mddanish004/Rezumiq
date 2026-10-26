import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle } from "lucide-react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, type AdminRevenue } from "@/lib/api";
import { Spinner } from "@/components/ui/Spinner";
import { formatDate, inr } from "@/lib/utils";
import {
  AdminMetric,
  BreakdownList,
  EmptyRow,
  Panel,
  RangeTabs,
  StatusBadge,
  axisStyle,
  delta,
  tooltipStyle,
} from "./shared";

export function AdminRevenueTab() {
  const [days, setDays] = useState(30);
  const revenue = useQuery<AdminRevenue>({
    queryKey: ["admin-revenue", days],
    queryFn: () => api.adminRevenue(days),
  });

  if (revenue.isLoading || !revenue.data) {
    return (
      <div className="grid place-items-center py-20">
        <Spinner label="Reading payments" />
      </div>
    );
  }
  if (revenue.isError) return <p className="text-sm text-danger">Revenue could not be loaded.</p>;

  const data = revenue.data;
  const totals = data.totals;
  const conversion = totals.checkouts ? Math.round((totals.checkoutsPaid / totals.checkouts) * 100) : 0;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-muted">Dodo Payments, GST included. Refunds leave the captured total.</p>
        <RangeTabs days={days} onChange={setDays} />
      </div>

      {!data.dodoConfigured ? (
        <div className="flex items-start gap-2 rounded-card border border-warning/25 bg-warning/5 p-4 text-sm text-warning">
          <AlertCircle size={15} className="mt-0.5" />
          Dodo is not configured on this API. Checkouts and webhooks are disabled.
        </div>
      ) : null}

      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <AdminMetric
          label="Revenue"
          value={inr(totals.paise)}
          delta={delta(totals.paise, totals.previousPaise)}
          hint={`${inr(totals.previousPaise)} previously`}
        />
        <AdminMetric label="All time" value={inr(totals.allTimePaise)} hint="Captured, refunds removed" />
        <AdminMetric label="Payers" value={totals.payers} hint={`${totals.checkoutsPaid} of ${totals.checkouts} checkouts paid`} />
        <AdminMetric label="Conversion" value={`${conversion}%`} hint="Checkout to payment" />
      </div>

      <Panel title="Revenue over time" description="Captured payments per day.">
        <div className="h-[220px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.byDay} margin={{ top: 4, right: 8, left: -12, bottom: 0 }}>
              <defs>
                <linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#141414" stopOpacity={0.16} />
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
              <YAxis
                tick={axisStyle}
                tickLine={false}
                axisLine={false}
                width={55}
                tickFormatter={(value: number) => `₹${Math.round(value / 100)}`}
              />
              <Tooltip
                contentStyle={tooltipStyle}
                labelStyle={{ color: "#66645E", fontSize: 10 }}
                formatter={(value) => [inr(Number(value)), "Revenue"]}
              />
              <Area type="monotone" dataKey="paise" name="Revenue" stroke="#141414" strokeWidth={1.5} fill="url(#revenueFill)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Active subscriptions" description="People paying right now.">
          <BreakdownList
            items={data.activeSubscriptions.map((row) => ({
              label: row.plan === "pro" ? "Pro" : "Season Pass",
              count: row.active,
            }))}
            empty="No active paid subscriptions."
          />
        </Panel>
        <Panel title="Payment statuses" description="All attempts in this period.">
          <BreakdownList items={data.statuses} empty="No payment attempts." />
        </Panel>
      </div>

      <Panel title="Payments" description="Newest first.">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[700px] text-left text-[12px] [&_td]:pr-3 [&_th]:pr-3">
            <thead>
              <tr className="border-b border-line font-mono text-[9px] uppercase tracking-[0.1em] text-muted">
                <th className="pb-2 font-normal">Person</th>
                <th className="pb-2 font-normal">Plan</th>
                <th className="pb-2 text-right font-normal">Amount</th>
                <th className="pb-2 font-normal">Status</th>
                <th className="pb-2 font-normal">Method</th>
                <th className="pb-2 text-right font-normal">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {data.payments.length ? (
                data.payments.map((payment) => (
                  <tr key={payment.id}>
                    <td className="max-w-[240px] truncate py-2.5 font-mono text-[10px]">{payment.email}</td>
                    <td className="py-2.5 text-muted">{payment.plan === "pro" ? "Pro" : payment.plan === "season_pass" ? "Season Pass" : "—"}</td>
                    <td className="py-2.5 text-right font-mono">{inr(payment.amountPaise)}</td>
                    <td className="py-2.5">
                      <StatusBadge status={payment.status} />
                    </td>
                    <td className="py-2.5 text-muted">{payment.method || "—"}</td>
                    <td className="py-2.5 text-right font-mono text-[10px] text-muted">{formatDate(payment.createdAt)}</td>
                  </tr>
                ))
              ) : (
                <EmptyRow colSpan={6}>No payments in this period.</EmptyRow>
              )}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
