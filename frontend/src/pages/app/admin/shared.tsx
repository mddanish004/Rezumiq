import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function AdminMetric({
  label,
  value,
  hint,
  delta,
}: {
  label: string;
  value: string | number;
  hint?: string;
  delta?: number | null;
}) {
  return (
    <div className="rounded-card border border-line bg-surface p-4 shadow-soft">
      <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">{label}</p>
      <div className="mt-1 flex items-baseline gap-2">
        <p className="font-display text-[26px] leading-none">{value}</p>
        {delta !== undefined && delta !== null && Number.isFinite(delta) ? (
          <span className={cn("font-mono text-[10px]", delta >= 0 ? "text-success" : "text-danger")}>
            {delta >= 0 ? "+" : ""}
            {delta}%
          </span>
        ) : null}
      </div>
      {hint ? <p className="mt-1.5 truncate text-[11px] text-muted">{hint}</p> : null}
    </div>
  );
}

export function Panel({
  title,
  description,
  action,
  children,
  className,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("rounded-card border border-line bg-surface p-5 shadow-soft", className)}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="font-display text-xl leading-tight">{title}</h2>
          {description ? <p className="mt-0.5 max-w-xl text-[12px] leading-5 text-muted">{description}</p> : null}
        </div>
        {action}
      </div>
      <div className="mt-4">{children}</div>
    </section>
  );
}

export function RangeTabs({ days, onChange }: { days: number; onChange: (days: number) => void }) {
  return (
    <div className="flex gap-1 rounded-field border border-line bg-surface p-1">
      {[7, 30, 90].map((range) => (
        <button
          key={range}
          type="button"
          onClick={() => onChange(range)}
          className={cn(
            "rounded px-2.5 py-1 text-[11px] transition-colors",
            days === range ? "bg-ink text-paper" : "text-muted hover:text-ink",
          )}
        >
          {range}d
        </button>
      ))}
    </div>
  );
}

export function BreakdownList({
  items,
  empty = "Nothing in this period.",
  formatValue = (count: number) => String(count),
}: {
  items: Array<{ label: string; count: number; key?: string }>;
  empty?: string;
  formatValue?: (count: number) => string;
}) {
  const max = Math.max(1, ...items.map((item) => item.count));
  if (!items.length) return <p className="text-[12px] text-muted">{empty}</p>;
  return (
    <div className="space-y-2.5">
      {items.map((item) => (
        <div key={item.key ?? item.label}>
          <div className="flex items-center justify-between gap-3 text-[12px]">
            <span className="truncate text-muted">{item.label}</span>
            <span className="font-mono text-[11px]">{formatValue(item.count)}</span>
          </div>
          <div className="mt-1 h-[3px] overflow-hidden rounded-full bg-line">
            <div className="h-full rounded-full bg-forest/60" style={{ width: `${(item.count / max) * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

export function Funnel({
  steps,
}: {
  steps: Array<{ label: string; value: number }>;
}) {
  const top = Math.max(1, steps[0]?.value ?? 1);
  return (
    <div className="space-y-2.5">
      {steps.map((step) => (
        <div key={step.label} className="flex items-center gap-3">
          <span className="w-24 shrink-0 text-[11px] text-muted">{step.label}</span>
          <div className="h-6 flex-1 overflow-hidden rounded bg-paper">
            <div
              className="flex h-full items-center rounded bg-forest/15 px-2 font-mono text-[10px] text-forest"
              style={{ width: `${Math.max(6, (step.value / top) * 100)}%` }}
            >
              {step.value}
            </div>
          </div>
          <span className="w-10 shrink-0 text-right font-mono text-[10px] text-muted">
            {top ? Math.round((step.value / top) * 100) : 0}%
          </span>
        </div>
      ))}
    </div>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const tone =
    status === "active" || status === "captured" || status === "succeeded"
      ? "success"
      : status === "failed" || status === "past_due"
        ? "danger"
        : status === "cancelled" || status === "expired" || status === "refunded"
          ? "warning"
          : "outline";
  return (
    <span
      className={cn(
        "inline-flex rounded-full border px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.1em]",
        tone === "success" && "border-success/20 bg-success/10 text-success",
        tone === "danger" && "border-danger/20 bg-danger/10 text-danger",
        tone === "warning" && "border-warning/20 bg-warning/10 text-warning",
        tone === "outline" && "border-line text-muted",
      )}
    >
      {status.replaceAll("_", " ")}
    </span>
  );
}

export function EmptyRow({ colSpan, children }: { colSpan: number; children: ReactNode }) {
  return (
    <tr>
      <td colSpan={colSpan} className="py-6 text-center text-[12px] text-muted">
        {children}
      </td>
    </tr>
  );
}

export function delta(now: number, before: number) {
  if (!before) return now ? 100 : 0;
  return Math.round(((now - before) / before) * 100);
}

export function formatNumber(value: number) {
  return new Intl.NumberFormat("en-IN").format(value);
}

export function formatBytes(bytes: number) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = Math.min(units.length - 1, Math.floor(Math.log(bytes) / Math.log(1024)));
  return `${(bytes / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

export function formatDuration(seconds: number) {
  const days = Math.floor(seconds / 86_400);
  const hours = Math.floor((seconds % 86_400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days) return `${days}d ${hours}h`;
  if (hours) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export const tooltipStyle = {
  borderRadius: 8,
  border: "1px solid #E3DFD6",
  fontSize: 12,
  boxShadow: "0 8px 24px rgba(20,20,20,0.08)",
} as const;

export const axisStyle = { fontSize: 10, fill: "#66645E" } as const;
