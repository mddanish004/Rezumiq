import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Clock, RotateCcw, Tag, X } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { Version, VersionDetail } from "@/lib/resume";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { formatRelative } from "@/lib/utils";

const kindTone: Record<string, "neutral" | "success" | "lime" | "outline" | "dark"> = {
  manual: "neutral",
  named: "lime",
  ai: "success",
  restore: "outline",
  import: "dark",
};

export function VersionDrawer({
  open,
  onOpenChange,
  resumeId,
  headVersionId,
  onRestored,
  onCheckpoint,
  saving,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  resumeId: string;
  headVersionId: string | null;
  onRestored: (version: VersionDetail) => void;
  onCheckpoint: (label: string) => Promise<void>;
  saving: boolean;
}) {
  const [label, setLabel] = useState("");
  const queryClient = useQueryClient();
  const versions = useQuery<Version[]>({
    queryKey: ["versions", resumeId],
    queryFn: () => api.versions(resumeId),
    enabled: open,
  });

  const restore = useMutation({
    mutationFn: (versionId: string) => api.restoreVersion(resumeId, versionId),
    onSuccess: (version) => {
      onRestored(version);
      void queryClient.invalidateQueries({ queryKey: ["versions", resumeId] });
      toast.success("Version restored as a new head");
      onOpenChange(false);
    },
    onError: (error) => toast.error(error.message),
  });

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-ink/25 backdrop-blur-[2px]" />
        <Dialog.Content className="fixed right-0 top-0 z-50 flex h-full w-[min(460px,100vw)] flex-col border-l border-line bg-surface shadow-lift">
          <div className="flex items-start justify-between border-b border-line px-5 py-4">
            <div>
              <Dialog.Title className="font-display text-2xl">Version history</Dialog.Title>
              <Dialog.Description className="mt-1 text-xs text-muted">
                Every save is a snapshot. Restoring one creates a new version, never overwrites.
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button
                type="button"
                className="focus-ring grid h-8 w-8 place-items-center rounded-field text-muted hover:bg-soft"
                aria-label="Close history"
              >
                <X size={16} />
              </button>
            </Dialog.Close>
          </div>

          <div className="border-b border-line p-4">
            <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">Name a checkpoint</p>
            <form
              className="mt-2 flex gap-2"
              onSubmit={async (event) => {
                event.preventDefault();
                if (!label.trim()) return;
                await onCheckpoint(label.trim());
                setLabel("");
                void queryClient.invalidateQueries({ queryKey: ["versions", resumeId] });
              }}
            >
              <input
                value={label}
                onChange={(event) => setLabel(event.target.value)}
                placeholder="Before tailoring to Stripe"
                className="focus-ring h-9 flex-1 rounded-field border border-line bg-paper px-2.5 text-[13px]"
              />
              <Button size="sm" type="submit" disabled={!label.trim() || saving}>
                <Tag size={12} /> Save
              </Button>
            </form>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {versions.isLoading ? (
              <Spinner label="Loading versions" />
            ) : versions.data?.length ? (
              <ol className="relative space-y-3 border-l border-line pl-4">
                {versions.data.map((version) => (
                  <li key={version.id} className="relative">
                    <span className="absolute -left-[21px] top-2 h-2 w-2 rounded-full border border-line bg-paper" />
                    <div className="rounded-field border border-line bg-paper/50 p-3">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <Badge tone={kindTone[version.kind] ?? "neutral"}>{version.kind}</Badge>
                        {version.semver ? <Badge tone="outline">v{version.semver}</Badge> : null}
                        {version.id === headVersionId ? <Badge tone="success">Current head</Badge> : null}
                      </div>
                      {version.label ? <p className="mt-2 text-[13px] font-medium">{version.label}</p> : null}
                      <p className="mt-1 flex items-center gap-1.5 text-[11px] text-muted">
                        <Clock size={11} /> {formatRelative(version.createdAt)}
                      </p>
                      {version.id !== headVersionId ? (
                        <Button
                          size="sm"
                          variant="secondary"
                          className="mt-2 h-7 px-2 text-[11px]"
                          disabled={restore.isPending}
                          onClick={() => {
                            if (window.confirm("Restore this version as the new head?")) restore.mutate(version.id);
                          }}
                        >
                          <RotateCcw size={11} /> Restore
                        </Button>
                      ) : null}
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="text-sm text-muted">No versions yet.</p>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
