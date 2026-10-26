import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { useMutation } from "@tanstack/react-query";
import { Gauge, X } from "lucide-react";
import { toast } from "sonner";
import { api, type AtsReportData, type Job } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export function AtsDialog({
  open,
  onOpenChange,
  resumeId,
  jobs,
  onChecked,
  beforeRun,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  resumeId: string;
  jobs: Job[];
  onChecked?: (report: AtsReportData) => void;
  beforeRun?: () => Promise<void>;
}) {
  const [jobId, setJobId] = useState("");
  const [report, setReport] = useState<AtsReportData | null>(null);

  const run = useMutation({
    mutationFn: async () => {
      await beforeRun?.();
      return api.atsReport(resumeId, jobId || undefined);
    },
    onSuccess: (data) => {
      setReport(data);
      onChecked?.(data);
      toast.success(`ATS score ${data.score}`);
    },
    onError: (error) => toast.error(error.message),
  });

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-ink/25 backdrop-blur-[2px]" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 flex max-h-[86vh] w-[min(640px,calc(100vw-2rem))] -translate-x-1/2 -translate-y-1/2 flex-col rounded-card border border-line bg-surface shadow-lift">
          <div className="flex items-start justify-between border-b border-line px-5 py-4">
            <div>
              <Dialog.Title className="flex items-center gap-2 font-display text-2xl">
                <Gauge size={17} /> ATS check
              </Dialog.Title>
              <Dialog.Description className="mt-1 text-xs text-muted">
                The PDF is compiled and read back through a parser. The latest score is saved on this resume.
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button type="button" className="focus-ring grid h-8 w-8 place-items-center rounded-field text-muted hover:bg-soft" aria-label="Close ATS">
                <X size={16} />
              </button>
            </Dialog.Close>
          </div>
          <div className="flex-1 overflow-y-auto p-5">
            <div className="flex flex-wrap items-end gap-2">
              <label className="min-w-0 flex-1">
                <span className="mb-1 block font-mono text-[9px] uppercase tracking-[0.12em] text-muted">Job post (optional)</span>
                <select
                  value={jobId}
                  onChange={(event) => setJobId(event.target.value)}
                  className="focus-ring h-10 w-full rounded-field border border-line bg-paper px-3 text-[13px]"
                >
                  <option value="">No job, general check</option>
                  {jobs.map((job) => (
                    <option key={job.id} value={job.id}>
                      {[job.company, job.role].filter(Boolean).join(" · ") || "Saved posting"}
                    </option>
                  ))}
                </select>
              </label>
              <Button onClick={() => run.mutate()} disabled={run.isPending}>
                {run.isPending ? "Reading..." : "Run check"}
              </Button>
            </div>

            {report ? (
              <div className="mt-5">
                <div className="flex items-end gap-4">
                  <p className="font-display text-6xl leading-none">{report.score}</p>
                  <div className="pb-1">
                    <Badge tone={report.grade === "excellent" || report.grade === "good" ? "success" : "warning"}>
                      {report.grade}
                    </Badge>
                    <p className="mt-2 max-w-lg text-xs leading-5 text-muted">{report.summary}</p>
                  </div>
                </div>
                <div className="mt-5 space-y-2">
                  {report.categories.map((category) => (
                    <div key={category.id} className="flex items-center justify-between rounded-field border border-line bg-paper/50 px-3 py-2 text-[12px]">
                      <span>{category.label}</span>
                      <span className="font-mono text-[10px] text-muted">{category.score} / {category.maxScore}</span>
                    </div>
                  ))}
                </div>
                {report.keywords ? (
                  <div className="mt-4">
                    <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">Keywords</p>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {report.keywords.matched.map((skill) => <Badge key={skill} tone="success">{skill}</Badge>)}
                      {report.keywords.missing.map((skill) => <Badge key={skill} tone="danger">{skill}</Badge>)}
                    </div>
                  </div>
                ) : null}
                <p className="mt-4 text-[10px] text-muted">
                  The full report with check-level fixes is available from the ATS page.
                </p>
              </div>
            ) : null}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
