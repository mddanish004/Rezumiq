import { useQuery } from "@tanstack/react-query";
import { Check, ExternalLink, X } from "lucide-react";
import { api, type AdminSystem, type AdminTraffic } from "@/lib/api";
import { Spinner } from "@/components/ui/Spinner";
import { formatDate } from "@/lib/utils";
import { AdminMetric, Panel, StatusBadge, formatBytes, formatDuration, formatNumber } from "./shared";

export function AdminSystemTab() {
  const system = useQuery<AdminSystem>({ queryKey: ["admin-system"], queryFn: api.adminSystem });
  const traffic = useQuery<AdminTraffic>({
    queryKey: ["admin-traffic"],
    queryFn: api.adminTraffic,
    retry: false,
  });

  if (system.isLoading || !system.data) {
    return (
      <div className="grid place-items-center py-20">
        <Spinner label="Checking the system" />
      </div>
    );
  }
  if (system.isError) return <p className="text-sm text-danger">System status could not be loaded.</p>;

  const data = system.data;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <AdminMetric label="Environment" value={data.api.environment} hint={data.api.nodeVersion} />
        <AdminMetric label="Uptime" value={formatDuration(data.api.uptimeSeconds)} hint="Since the last restart" />
        <AdminMetric label="Memory" value={formatBytes(data.api.rssBytes)} hint="Process RSS" />
        <AdminMetric
          label="Compiler"
          value={data.compiler.ok ? "Ready" : "Down"}
          hint={`${data.compiler.mode}${data.compiler.latencyMs ? ` · ${data.compiler.latencyMs}ms` : ""}`}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Database" description="The row that keeps every resume and view.">
          <div className="grid grid-cols-2 gap-3 text-[12px]">
            <div>
              <p className="font-mono text-[9px] uppercase tracking-[0.1em] text-muted">Version</p>
              <p className="mt-0.5">{data.database.version || "—"}</p>
            </div>
            <div>
              <p className="font-mono text-[9px] uppercase tracking-[0.1em] text-muted">Size</p>
              <p className="mt-0.5">{formatBytes(data.database.sizeBytes)}</p>
            </div>
            <div>
              <p className="font-mono text-[9px] uppercase tracking-[0.1em] text-muted">Latency</p>
              <p className="mt-0.5">{data.database.latencyMs ? `${data.database.latencyMs}ms` : "—"}</p>
            </div>
            <div>
              <p className="font-mono text-[9px] uppercase tracking-[0.1em] text-muted">Connections</p>
              <p className="mt-0.5">
                {data.database.connections.map((row) => `${row.count} ${row.state}`).join(", ") || "—"}
              </p>
            </div>
          </div>
          {data.database.tables.length ? (
            <div className="mt-4 max-h-64 overflow-y-auto rounded-field border border-line">
              <table className="w-full text-left text-[12px]">
                <thead className="sticky top-0 bg-paper">
                  <tr className="border-b border-line font-mono text-[9px] uppercase tracking-[0.1em] text-muted">
                    <th className="px-2 py-1.5 font-normal">Table</th>
                    <th className="px-2 py-1.5 text-right font-normal">Rows</th>
                    <th className="px-2 py-1.5 text-right font-normal">Size</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {data.database.tables.map((table) => (
                    <tr key={table.name}>
                      <td className="px-2 py-1.5 font-mono text-[10px]">{table.name}</td>
                      <td className="px-2 py-1.5 text-right font-mono">{formatNumber(table.rows)}</td>
                      <td className="px-2 py-1.5 text-right font-mono text-muted">{formatBytes(table.sizeBytes)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </Panel>

        <Panel title="Operations" description="Backups and provider readiness.">
          <div className="space-y-3">
            <div className="flex items-center justify-between rounded-field border border-line bg-paper/40 px-3 py-2">
              <div>
                <p className="text-[12px] font-medium">Last webhook</p>
                <p className="text-[10px] text-muted">Dodo subscription and payment events</p>
              </div>
              <span className="font-mono text-[10px] text-muted">
                {data.lastWebhookAt ? formatDate(data.lastWebhookAt) : "Never received"}
              </span>
            </div>
            <div className="flex items-center justify-between rounded-field border border-line bg-paper/40 px-3 py-2">
              <div>
                <p className="text-[12px] font-medium">Backup</p>
                <p className="text-[10px] text-muted">Latest object in the backup bucket</p>
              </div>
              <span className="font-mono text-[10px] text-muted">
                {data.backup ? `${data.backup.key} · ${formatBytes(data.backup.sizeBytes)}` : "Not configured"}
              </span>
            </div>
            <div>
              <p className="font-mono text-[9px] uppercase tracking-[0.1em] text-muted">Integrations</p>
              <div className="mt-2 grid gap-1.5 sm:grid-cols-2">
                {data.integrations.map((integration) => (
                  <div key={integration.name} className="flex items-center gap-1.5 text-[12px]">
                    {integration.configured ? (
                      <Check size={12} className="text-success" />
                    ) : (
                      <X size={12} className="text-muted" />
                    )}
                    <span className={integration.configured ? "" : "text-muted"}>{integration.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Panel>
      </div>

      <Panel title="Product analytics" description="PostHog events and admin reads.">
        {traffic.isLoading ? (
          <p className="text-[12px] text-muted">Checking PostHog...</p>
        ) : traffic.data?.configured ? (
          <div className="flex flex-wrap items-center gap-2 text-[12px]">
            <StatusBadge status="active" />
            <span>PostHog is configured.</span>
            <a
              href={traffic.data.dashboardUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 underline decoration-line underline-offset-2 hover:text-ink"
            >
              Open the dashboard <ExternalLink size={11} />
            </a>
          </div>
        ) : (
          <p className="text-[12px] text-muted">
            {traffic.data?.error || "PostHog is not configured. Set POSTHOG_KEY and POSTHOG_PROJECT_ID to read traffic."}
          </p>
        )}
      </Panel>
    </div>
  );
}
