import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as Dialog from "@radix-ui/react-dialog";
import { Briefcase, Link2, Plus, Trash2, X } from "lucide-react";
import { toast } from "sonner";
import { api, type Job } from "@/lib/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Spinner } from "@/components/ui/Spinner";
import { formatRelative } from "@/lib/utils";

export default function Jobs() {
  const [adding, setAdding] = useState(false);
  const jobs = useQuery<Job[]>({ queryKey: ["jobs"], queryFn: api.jobs });
  const queryClient = useQueryClient();

  const remove = useMutation({
    mutationFn: (id: string) => api.deleteJob(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
      toast.success("Job removed");
    },
    onError: (error) => toast.error(error.message),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Workspace / Jobs"
        title="Saved job posts."
        description="Paste a description or a URL once. Tailoring, ATS checks, and coverage reuse the same parsed requirements."
        actions={
          <Button size="sm" onClick={() => setAdding(true)}>
            <Plus size={14} /> Add job post
          </Button>
        }
      />

      {jobs.isLoading ? (
        <div className="grid place-items-center py-20">
          <Spinner label="Loading jobs" />
        </div>
      ) : jobs.data?.length ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {jobs.data.map((job) => (
            <Card key={job.id} className="p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-muted">
                      {job.company || "Saved posting"}
                    </p>
                    {job.latestMatch ? (
                      <Badge tone="success">{job.latestMatch.percent}% match</Badge>
                    ) : (
                      <Badge tone="outline">Not checked</Badge>
                    )}
                  </div>
                  <p className="mt-1 truncate text-base font-medium">{job.role || "Job description"}</p>
                  <p className="mt-1 flex items-center gap-1.5 text-xs text-muted">
                    {job.sourceUrl ? <Link2 size={12} /> : <Briefcase size={12} />}
                    {job.sourceUrl ? "Imported from a URL" : "Pasted description"} · {formatRelative(job.createdAt)}
                  </p>
                </div>
                <button
                  type="button"
                  className="focus-ring grid h-8 w-8 shrink-0 place-items-center rounded-field text-muted hover:bg-danger/5 hover:text-danger"
                  aria-label="Delete job"
                  onClick={() => {
                    if (window.confirm("Remove this saved job post?")) remove.mutate(job.id);
                  }}
                >
                  <Trash2 size={14} />
                </button>
              </div>
              <div className="mt-4 flex flex-wrap gap-2 border-t border-line pt-4">
                <Link to="/app/resumes">
                  <Button size="sm" variant="secondary">
                    Tailor a resume
                  </Button>
                </Link>
                <Link to="/app/ats">
                  <Button size="sm" variant="ghost">
                    Check ATS
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<Briefcase size={20} />}
          title="No job posts saved"
          description="Save a posting before you tailor. The parsed requirements stay attached to every check."
          action={
            <Button size="sm" onClick={() => setAdding(true)}>
              <Plus size={14} /> Add a job post
            </Button>
          }
        />
      )}

      <AddJobDialog open={adding} onOpenChange={setAdding} />
    </div>
  );
}

function AddJobDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (value: boolean) => void }) {
  const [mode, setMode] = useState<"text" | "url">("text");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const queryClient = useQueryClient();

  const add = useMutation({
    mutationFn: () => (mode === "url" ? api.createJobFromUrl(url.trim()) : api.createJob(text.trim())),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
      await queryClient.invalidateQueries({ queryKey: ["usage"] });
      toast.success("Job saved and parsed");
      setText("");
      setUrl("");
      onOpenChange(false);
    },
    onError: (error) => toast.error(error.message),
  });

  const valid = mode === "url" ? /^https?:\/\//.test(url.trim()) : text.trim().length >= 50;

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-ink/30 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[min(600px,calc(100vw-2rem))] -translate-x-1/2 -translate-y-1/2 rounded-card border border-line bg-surface p-6 shadow-lift">
          <div className="flex items-start justify-between gap-4">
            <div>
              <Dialog.Title className="font-display text-2xl">Add a job post</Dialog.Title>
              <Dialog.Description className="mt-1 text-sm text-muted">
                One posting, saved once. We extract the company, role, and requirements.
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button type="button" className="focus-ring grid h-8 w-8 place-items-center rounded-field text-muted hover:bg-soft" aria-label="Close">
                <X size={16} />
              </button>
            </Dialog.Close>
          </div>
          <div className="mt-5 flex gap-1 border-b border-line">
            {(["text", "url"] as const).map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => setMode(value)}
                className={`border-b-2 px-3 py-2 text-[13px] capitalize ${
                  mode === value ? "border-ink font-medium text-ink" : "border-transparent text-muted"
                }`}
              >
                {value === "text" ? "Paste text" : "From URL"}
              </button>
            ))}
          </div>
          <form
            className="mt-4 space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              if (valid) add.mutate();
            }}
          >
            {mode === "text" ? (
              <label className="block">
                <span className="mb-1.5 block font-mono text-[10px] uppercase tracking-[0.16em] text-muted">
                  Job description
                </span>
                <textarea
                  value={text}
                  onChange={(event) => setText(event.target.value)}
                  rows={9}
                  placeholder="Paste the full job description here. At least 50 characters."
                  className="focus-ring w-full resize-y rounded-field border border-line bg-paper p-3 text-sm leading-6"
                />
                <span className="mt-1 block text-right font-mono text-[9px] text-muted">{text.length} chars</span>
              </label>
            ) : (
              <label className="block">
                <span className="mb-1.5 block font-mono text-[10px] uppercase tracking-[0.16em] text-muted">
                  Job URL
                </span>
                <input
                  value={url}
                  onChange={(event) => setUrl(event.target.value)}
                  placeholder="https://company.com/careers/role"
                  className="focus-ring h-11 w-full rounded-field border border-line bg-paper px-3.5 text-sm"
                />
                <span className="mt-1 block text-xs text-muted">
                  The page is read as text. If it fails, paste the description instead.
                </span>
              </label>
            )}
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={!valid || add.isPending}>
                {add.isPending ? "Parsing..." : "Save and parse"}
              </Button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
