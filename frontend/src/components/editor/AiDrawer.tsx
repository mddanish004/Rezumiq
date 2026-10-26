import { useEffect, useMemo, useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { Link } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { ArrowRight, Check, Sparkles, X } from "lucide-react";
import { toast } from "sonner";
import { api, ApiError, type Job, type Suggestion, type SuggestionOperation } from "@/lib/api";
import type { Content, VersionDetail } from "@/lib/resume";
import { bulletText, sectionById } from "@/lib/resume";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";

type Mode = "edit" | "tailor" | "fix";

export function AiDrawer({
  open,
  onOpenChange,
  resumeId,
  content,
  jobs,
  initialTargetIds,
  targetLabel,
  onApplied,
  codeMode = false,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  resumeId: string;
  content: Content;
  jobs: Job[];
  initialTargetIds?: string[];
  targetLabel?: string;
  onApplied: (version: VersionDetail) => void;
  codeMode?: boolean;
}) {
  const [mode, setMode] = useState<Mode>(codeMode ? "fix" : "edit");
  const [instruction, setInstruction] = useState("");
  const [jobId, setJobId] = useState(jobs[0]?.id ?? "");
  const [suggestion, setSuggestion] = useState<Suggestion | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const targetKey = initialTargetIds?.join(",") ?? "";
  const jobsKey = jobs.map((job) => job.id).join(",");

  useEffect(() => {
    if (!open) return;
    setSuggestion(null);
    setInstruction("");
    setMode(codeMode ? "fix" : initialTargetIds?.length ? "edit" : jobs.length ? "tailor" : "edit");
    setJobId(jobs[0]?.id ?? "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, targetKey, jobsKey, codeMode]);

  const generate = useMutation({
    mutationFn: () => {
      if (mode === "fix") {
        return api.createSuggestion(resumeId, { type: "fix_compile" });
      }
      if (mode === "tailor") {
        if (!jobId) throw new Error("Save a job post first, then tailor to it.");
        return api.createSuggestion(resumeId, {
          type: "tailor",
          jobId,
          ...(instruction.trim() ? { instructions: instruction.trim() } : {}),
        });
      }
      if (instruction.trim().length < 3) throw new Error("Describe the edit in a few words first.");
      return api.createSuggestion(resumeId, {
        type: "edit",
        instruction: instruction.trim(),
        ...(initialTargetIds?.length ? { targetIds: initialTargetIds } : {}),
      });
    },
    onSuccess: (data) => {
      setSuggestion(data);
      setSelected(new Set(data.operations.map((operation) => operation.id)));
    },
    onError: (error) => toast.error(error.message),
  });

  const apply = useMutation({
    mutationFn: () => api.applySuggestion(resumeId, suggestion!.id, [...selected]),
    onSuccess: (data) => {
      onApplied(data.version);
      toast.success("Suggestion applied as a new version");
      onOpenChange(false);
    },
    onError: (error) => toast.error(error.message),
  });

  const error = generate.error as Error | null;
  const isQuota = error instanceof ApiError && error.status === 402;
  const noKey = error instanceof ApiError && error.status === 503;

  const operations = useMemo(
    () => suggestion?.operations.map((operation) => describe(operation, content)) ?? [],
    [suggestion, content],
  );

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-ink/25 backdrop-blur-[2px]" />
        <Dialog.Content className="fixed right-0 top-0 z-50 flex h-full w-[min(560px,100vw)] flex-col border-l border-line bg-surface shadow-lift">
          <div className="flex items-start justify-between border-b border-line px-5 py-4">
            <div>
              <Dialog.Title className="flex items-center gap-2 font-display text-2xl">
                <Sparkles size={17} /> Ask AI
              </Dialog.Title>
              <Dialog.Description className="mt-1 text-xs text-muted">
                Nothing is applied until you choose the changes you want.
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button type="button" className="focus-ring grid h-8 w-8 place-items-center rounded-field text-muted hover:bg-soft" aria-label="Close AI">
                <X size={16} />
              </button>
            </Dialog.Close>
          </div>

          <div className="flex-1 overflow-y-auto p-5">
            {codeMode ? (
              <div className="rounded-field border border-forest/20 bg-forest/5 px-3 py-2 text-xs leading-5 text-forest">
                The model reads the current LaTeX and returns the complete document with the compile problem
                fixed. Your resume facts stay unchanged.
              </div>
            ) : (
            <div className="flex gap-1 border-b border-line">
              {(["tailor", "edit"] as const).map((value) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => {
                    setMode(value);
                    setSuggestion(null);
                  }}
                  className={cn(
                    "border-b-2 px-3 py-2 text-[13px] capitalize",
                    mode === value ? "border-ink font-medium text-ink" : "border-transparent text-muted",
                  )}
                >
                  {value === "tailor" ? "Tailor to a job" : "Edit with instructions"}
                </button>
              ))}
            </div>
            )}

            <div className="mt-4 space-y-3">
              {mode === "tailor" ? (
                jobs.length ? (
                  <label className="block">
                    <span className="mb-1 block font-mono text-[9px] uppercase tracking-[0.12em] text-muted">
                      Job post
                    </span>
                    <select
                      value={jobId}
                      onChange={(event) => setJobId(event.target.value)}
                      className="focus-ring h-10 w-full rounded-field border border-line bg-paper px-3 text-[13px]"
                    >
                      {jobs.map((job) => (
                        <option key={job.id} value={job.id}>
                          {[job.company, job.role].filter(Boolean).join(" · ") || "Saved posting"}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : (
                  <div className="rounded-field border border-dashed border-line p-3 text-sm text-muted">
                    Save a job post first.{" "}
                    <Link to="/app/jobs" className="underline decoration-line underline-offset-2 hover:text-ink">
                      Add one now
                    </Link>
                    .
                  </div>
                )
              ) : null}

              {initialTargetIds?.length ? (
                <div className="flex items-center gap-2 rounded-field border border-forest/20 bg-forest/5 px-3 py-2 text-xs text-forest">
                  <Check size={12} /> Scope: {targetLabel ?? "selected section"}
                </div>
              ) : null}

              {mode !== "fix" ? (
              <label className="block">
                <span className="mb-1 block font-mono text-[9px] uppercase tracking-[0.12em] text-muted">
                  {mode === "tailor" ? "Extra instructions (optional)" : "What should change?"}
                </span>
                <textarea
                  value={instruction}
                  onChange={(event) => setInstruction(event.target.value)}
                  rows={3}
                  placeholder={
                    mode === "tailor"
                      ? "Emphasise distributed systems and billing scale."
                      : "Tighten the summary to two sentences."
                  }
                  className="focus-ring w-full resize-y rounded-field border border-line bg-paper p-3 text-[13px] leading-6"
                />
              </label>
              ) : null}

              <Button
                className="w-full"
                onClick={() => generate.mutate()}
                disabled={
                  generate.isPending ||
                  (mode === "tailor" ? !jobId : mode === "edit" ? instruction.trim().length < 3 : false)
                }
              >
                {generate.isPending
                  ? "Asking the model..."
                  : mode === "fix"
                    ? "Fix the LaTeX"
                    : "Generate changes"}
                {!generate.isPending ? <ArrowRight size={14} /> : null}
              </Button>

              {error ? (
                <div className="rounded-field border border-danger/20 bg-danger/5 p-3 text-sm text-danger">
                  <p>{error.message}</p>
                  {isQuota ? (
                    <Link to="/app/billing" className="mt-2 inline-flex items-center gap-1 text-xs font-medium underline decoration-danger/30 underline-offset-2">
                      Compare plans <ArrowRight size={12} />
                    </Link>
                  ) : null}
                  {noKey ? (
                    <Link to="/app/settings" className="mt-2 inline-flex items-center gap-1 text-xs font-medium underline decoration-danger/30 underline-offset-2">
                      Add an AI key <ArrowRight size={12} />
                    </Link>
                  ) : null}
                </div>
              ) : null}
            </div>

            {suggestion ? (
              <div className="mt-6 border-t border-line pt-5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-medium">{suggestion.summary}</p>
                  <Badge tone="lime">{suggestion.operations.length} changes</Badge>
                </div>
                <div className="mt-3 space-y-2">
                  {suggestion.operations.map((operation, index) => {
                    const detail = operations[index];
                    return (
                      <label
                        key={operation.id}
                        className={cn(
                          "block cursor-pointer rounded-field border p-3 transition-colors",
                          selected.has(operation.id)
                            ? "border-forest/30 bg-forest/5"
                            : "border-line bg-paper/50",
                        )}
                      >
                        <div className="flex items-start gap-2">
                          <input
                            type="checkbox"
                            checked={selected.has(operation.id)}
                            onChange={(event) => {
                              const next = new Set(selected);
                              if (event.target.checked) next.add(operation.id);
                              else next.delete(operation.id);
                              setSelected(next);
                            }}
                            className="mt-1 h-3.5 w-3.5 accent-[#1F5A46]"
                          />
                          <div className="min-w-0 flex-1">
                            <p className="text-[13px] font-medium">{detail.title}</p>
                            {detail.before ? (
                              <p className="mt-1 rounded bg-danger/5 px-2 py-1 text-[11px] leading-5 text-muted line-through decoration-danger/30">
                                {detail.before}
                              </p>
                            ) : null}
                            {detail.after ? (
                              <p className="mt-1 rounded bg-forest/5 px-2 py-1 text-[11px] leading-5 text-ink">
                                {detail.after}
                              </p>
                            ) : null}
                            {operation.reason ? <p className="mt-1 text-[11px] text-muted">{operation.reason}</p> : null}
                            {operation.flags.length ? (
                              <div className="mt-1.5 flex flex-wrap gap-1">
                                {operation.flags.map((flag) => (
                                  <Badge key={flag} tone="warning">{flag}</Badge>
                                ))}
                              </div>
                            ) : null}
                          </div>
                        </div>
                      </label>
                    );
                  })}
                </div>
                <div className="mt-4 flex items-center gap-2">
                  <Button
                    className="flex-1"
                    onClick={() => apply.mutate()}
                    disabled={!selected.size || apply.isPending}
                  >
                    {apply.isPending ? "Applying..." : `Apply ${selected.size} selected`}
                  </Button>
                  <Button variant="secondary" onClick={() => setSuggestion(null)}>
                    Discard
                  </Button>
                </div>
                <p className="mt-2 text-[10px] text-muted">
                  {suggestion.model || "Model pending"}
                  {suggestion.byok ? " · your key" : ""}
                  {suggestion.costUsdMicros === null ? "" : ` · $${(suggestion.costUsdMicros / 1_000_000).toFixed(4)}`}
                </p>
              </div>
            ) : null}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function describe(
  operation: SuggestionOperation,
  content: Content,
): { title: string; before?: string; after?: string } {
  if (operation.type === "update_bullet") {
    return {
      title: "Rewrite a bullet",
      before: bulletText(content, operation.bulletId ?? ""),
      after: operation.text ?? "",
    };
  }
  if (operation.type === "add_bullet") {
    return { title: "Add a bullet", after: operation.text ?? "" };
  }
  if (operation.type === "update_headline") {
    return { title: "Update the headline", before: content.basics.headline ?? "", after: operation.text ?? "" };
  }
  if (operation.type === "update_summary") {
    const section = operation.targetId ? sectionById(content, operation.targetId) : undefined;
    return { title: `Rewrite ${section?.title ?? "summary"}`, before: section?.text ?? "", after: operation.text ?? "" };
  }
  if (operation.type === "update_skills") {
    const section = content.sections.find((item) => (item.groups ?? []).some((group) => group.id === operation.groupId));
    const group = section?.groups?.find((item) => item.id === operation.groupId);
    return { title: `Update ${group?.name ?? "skill group"}`, after: (operation.items ?? []).join(", ") };
  }
  if (operation.type === "set_hidden") {
    return { title: operation.hidden ? "Hide an item" : "Show an item" };
  }
  if (operation.type === "set_space_after") {
    return { title: `Set spacing to ${operation.points ?? 0}pt` };
  }
  if (operation.type === "reorder") {
    return { title: "Reorder items" };
  }
  if (operation.type === "replace_source") {
    return { title: "Replace the LaTeX source", after: "Full document replaced" };
  }
  return { title: operation.type };
}
