import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type AdminContent } from "@/lib/api";
import { Spinner } from "@/components/ui/Spinner";
import {
  AdminMetric,
  BreakdownList,
  EmptyRow,
  Panel,
  RangeTabs,
  formatBytes,
  formatNumber,
} from "./shared";

export function AdminContentTab() {
  const [days, setDays] = useState(30);
  const content = useQuery<AdminContent>({
    queryKey: ["admin-content", days],
    queryFn: () => api.adminContent(days),
  });

  if (content.isLoading || !content.data) {
    return (
      <div className="grid place-items-center py-20">
        <Spinner label="Counting content" />
      </div>
    );
  }
  if (content.isError) return <p className="text-sm text-danger">Content stats could not be loaded.</p>;

  const data = content.data;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-muted">Stored content and how it is shared.</p>
        <RangeTabs days={days} onChange={setDays} />
      </div>

      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <AdminMetric
          label="Resumes"
          value={formatNumber(data.resumes.total)}
          hint={`${data.resumes.live} live · ${data.resumes.archived} archived · ${data.resumes.deleted} deleted`}
        />
        <AdminMetric
          label="Structured"
          value={formatNumber(data.resumes.structured)}
          hint={`${data.resumes.code} LaTeX · ${data.resumes.tailored} tailored`}
        />
        <AdminMetric
          label="Share links"
          value={formatNumber(data.sharing.links)}
          hint={`${data.sharing.listed} listed · ${data.sharing.protected} locked`}
        />
        <AdminMetric
          label="Share views"
          value={formatNumber(data.sharing.views)}
          hint={`${data.sharing.plain} plain links`}
        />
        <AdminMetric label="Jobs" value={formatNumber(data.jobs)} hint={`${data.jobsFromUrl} imported from a URL`} />
        <AdminMetric label="Uploads" value={formatNumber(data.uploads.files)} hint={formatBytes(data.uploads.bytes)} />
        <AdminMetric
          label="Templates"
          value={formatNumber(data.customTemplates)}
          hint="In the template registry"
        />
        <AdminMetric
          label="PDF imports"
          value={formatNumber(data.uploads.pdf)}
          hint={`${data.uploads.tex} LaTeX · ${data.uploads.text} text`}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Templates" description="Resumes per template.">
          <BreakdownList items={data.byTemplate} empty="No resumes yet." />
        </Panel>
        <Panel title="Version kinds" description="How each snapshot was made.">
          <BreakdownList items={data.versionKinds} empty="No versions yet." />
        </Panel>
      </div>

      <Panel title="Most viewed links" description="Public share links in this period.">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[620px] text-left text-[12px] [&_td]:pr-3 [&_th]:pr-3">
            <thead>
              <tr className="border-b border-line font-mono text-[9px] uppercase tracking-[0.1em] text-muted">
                <th className="pb-2 font-normal">Resume</th>
                <th className="pb-2 font-normal">Owner</th>
                <th className="pb-2 font-normal">Slug</th>
                <th className="pb-2 text-right font-normal">Views</th>
                <th className="pb-2 text-right font-normal">All time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {data.topLinks.length ? (
                data.topLinks.map((link) => (
                  <tr key={link.id}>
                    <td className="max-w-[220px] truncate py-2.5">{link.resumeTitle}</td>
                    <td className="py-2.5 font-mono text-[10px] text-muted">@{link.username}</td>
                    <td className="py-2.5 font-mono text-[10px] text-muted">/{link.slug}</td>
                    <td className="py-2.5 text-right font-mono">{link.views}</td>
                    <td className="py-2.5 text-right font-mono text-muted">{link.totalViews}</td>
                  </tr>
                ))
              ) : (
                <EmptyRow colSpan={5}>No links have been opened yet.</EmptyRow>
              )}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-[10px] text-muted">
          Uploads: {data.uploads.pdf} PDF · {data.uploads.tex} LaTeX · {data.uploads.text} text,{" "}
          {formatBytes(data.uploads.bytes)} total. Last {days} days for link views.
        </p>
      </Panel>
    </div>
  );
}
