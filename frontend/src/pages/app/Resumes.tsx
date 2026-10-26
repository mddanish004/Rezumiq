import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as Dialog from "@radix-ui/react-dialog";
import { Archive, Download, FileText, Plus, Share2, Trash2, Upload, X } from "lucide-react";
import { toast } from "sonner";
import { api, type Resume, type Template } from "@/lib/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Spinner } from "@/components/ui/Spinner";
import { formatRelative } from "@/lib/utils";
import { ShareDialog } from "@/components/share/ShareDialog";

export default function Resumes() {
  const [params, setParams] = useSearchParams();
  const [archived, setArchived] = useState(false);
  const [creating, setCreating] = useState(params.get("new") === "1");
  const [sharing, setSharing] = useState<Resume | null>(null);
  const resumes = useQuery<Resume[]>({
    queryKey: ["resumes", archived],
    queryFn: () => api.resumes(archived),
  });
  const templates = useQuery<Template[]>({ queryKey: ["templates"], queryFn: api.templates });
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const archive = useMutation({
    mutationFn: ({ id, value }: { id: string; value: boolean }) => api.archiveResume(id, value),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["resumes"] });
      toast.success(archived ? "Resume restored" : "Resume archived");
    },
    onError: (error) => toast.error(error.message),
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.deleteResume(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["resumes"] });
      toast.success("Resume deleted");
    },
    onError: (error) => toast.error(error.message),
  });

  const templateNames = new Map((templates.data ?? []).map((template) => [template.id, template.name]));
  const query = (params.get("q") ?? "").trim().toLowerCase();
  const visible = query
    ? (resumes.data ?? []).filter((resume) => resume.title.toLowerCase().includes(query))
    : (resumes.data ?? []);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Workspace / Resumes"
        title={archived ? "Archived resumes." : "Your resumes."}
        description={
          archived
            ? "Archived drafts are kept out of the active list. Restore one to keep editing it."
            : "Every resume keeps its own versions, template, target job, and last ATS check."
        }
        actions={
          <>
            <Link to="/app/import">
              <Button size="sm" variant="secondary">
                <Upload size={14} /> Import
              </Button>
            </Link>
            <Button size="sm" onClick={() => setCreating(true)}>
              <Plus size={14} /> New resume
            </Button>
          </>
        }
      />

      <div className="flex items-center gap-1 border-b border-line">
        <button
          type="button"
          onClick={() => setArchived(false)}
          className={`border-b-2 px-3 py-2 text-[13px] transition-colors ${
            archived ? "border-transparent text-muted hover:text-ink" : "border-ink font-medium text-ink"
          }`}
        >
          Active
        </button>
        <button
          type="button"
          onClick={() => setArchived(true)}
          className={`border-b-2 px-3 py-2 text-[13px] transition-colors ${
            archived ? "border-ink font-medium text-ink" : "border-transparent text-muted hover:text-ink"
          }`}
        >
          Archived
        </button>
        <span className="ml-auto pb-2 font-mono text-[10px] uppercase tracking-[0.1em] text-muted">
          {query ? `${visible.length} for "${query}"` : `${resumes.data?.length ?? 0} ${resumes.data?.length === 1 ? "resume" : "resumes"}`}
        </span>
      </div>

      {resumes.isLoading ? (
        <div className="grid place-items-center py-20">
          <Spinner label="Loading resumes" />
        </div>
      ) : visible.length ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {visible.map((resume) => (
            <Card key={resume.id} className="flex flex-col p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="grid h-10 w-10 place-items-center rounded-field border border-line bg-paper">
                  <FileText size={17} />
                </div>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    className="focus-ring grid h-8 w-8 place-items-center rounded-field text-muted hover:bg-soft hover:text-ink"
                    aria-label={archived ? "Restore resume" : "Archive resume"}
                    onClick={() => archive.mutate({ id: resume.id, value: !archived })}
                  >
                    <Archive size={14} />
                  </button>
                  <button
                    type="button"
                    className="focus-ring grid h-8 w-8 place-items-center rounded-field text-muted hover:bg-danger/5 hover:text-danger"
                    aria-label="Delete resume"
                    onClick={() => {
                      if (window.confirm(`Delete "${resume.title}" and all of its versions?`)) {
                        remove.mutate(resume.id);
                      }
                    }}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
              <p className="mt-4 text-[11px] text-muted">
                {resume.archivedAt ? `Archived ${formatRelative(resume.archivedAt)}` : `Updated ${formatRelative(resume.updatedAt)}`}
              </p>
              <p className="mt-0.5 truncate font-medium">{resume.title}</p>
              <div className="mt-2 flex flex-wrap items-center gap-1.5">
                <Badge tone={resume.mode === "code" ? "dark" : "neutral"}>
                  {resume.mode === "code" ? "LaTeX" : (resume.templateId && templateNames.get(resume.templateId)) || "Own LaTeX"}
                </Badge>
                {resume.latestAts ? (
                  <Badge tone="success">ATS {resume.latestAts.score}</Badge>
                ) : (
                  <Badge tone="outline">Not scored</Badge>
                )}
                <span className="font-mono text-[9px] uppercase tracking-[0.08em] text-muted">
                  Limit {resume.pageLimit}p
                </span>
              </div>
              <div className="mt-auto flex items-center gap-2 pt-5">
                <Link to={`/app/resumes/${resume.id}/edit`} className="flex-1">
                  <Button size="sm" variant="secondary" className="w-full">
                    Open editor
                  </Button>
                </Link>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setSharing(resume)}
                  aria-label="Share resume"
                  title="Share this resume"
                >
                  <Share2 size={14} />
                </Button>
                <a href={api.resumePdfUrl(resume.id)} target="_blank" rel="noreferrer">
                  <Button size="sm" variant="ghost" aria-label="Download PDF">
                    <Download size={14} />
                  </Button>
                </a>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<FileText size={20} />}
          title={query ? "No matching resumes" : archived ? "No archived resumes" : "No resumes yet"}
          description={
            query
              ? `Nothing matched "${query}". Try a shorter word, or clear the search.`
              : archived
                ? "Archived resumes will appear here. They stay available until you delete them."
                : "Create a blank resume, start from a template, or import a PDF or LaTeX file."
          }
          action={
            !archived ? (
              <div className="flex flex-wrap items-center gap-2">
                <Button size="sm" onClick={() => setCreating(true)}>
                  <Plus size={14} /> Create a resume
                </Button>
                <Link to="/app/import">
                  <Button size="sm" variant="secondary">
                    <Upload size={14} /> Import a file
                  </Button>
                </Link>
              </div>
            ) : undefined
          }
        />
      )}

      <CreateResumeDialog
        open={creating}
        onOpenChange={(value) => {
          setCreating(value);
          if (!value && params.get("new")) {
            const next = new URLSearchParams(params);
            next.delete("new");
            setParams(next, { replace: true });
          }
        }}
        templates={templates.data ?? []}
        onCreated={(resume) => navigate(`/app/resumes/${resume.id}/edit`)}
      />

      <ShareDialog
        open={Boolean(sharing)}
        onOpenChange={(value) => {
          if (!value) setSharing(null);
        }}
        resumeId={sharing?.id ?? ""}
        resumeTitle={sharing?.title ?? ""}
      />
    </div>
  );
}

function CreateResumeDialog({
  open,
  onOpenChange,
  templates,
  onCreated,
}: {
  open: boolean;
  onOpenChange: (value: boolean) => void;
  templates: Template[];
  onCreated: (resume: Resume) => void;
}) {
  const [title, setTitle] = useState("");
  const [templateId, setTemplateId] = useState("developer");
  const [mode, setMode] = useState<"structured" | "code">("structured");
  const create = useMutation({
    mutationFn: () => api.createResume(title.trim() || "Untitled resume", templateId, mode),
    onSuccess: (resume) => {
      toast.success("Resume created");
      onOpenChange(false);
      onCreated(resume);
    },
    onError: (error) => toast.error(error.message),
  });

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-ink/30 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[min(520px,calc(100vw-2rem))] -translate-x-1/2 -translate-y-1/2 rounded-card border border-line bg-surface p-6 shadow-lift">
          <div className="flex items-start justify-between gap-4">
            <div>
              <Dialog.Title className="font-display text-2xl">New resume</Dialog.Title>
              <Dialog.Description className="mt-1 text-sm text-muted">
                Start blank with a template, or import a PDF or LaTeX file from the Import screen.
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button
                type="button"
                className="focus-ring grid h-8 w-8 place-items-center rounded-field text-muted hover:bg-soft"
                aria-label="Close"
              >
                <X size={16} />
              </button>
            </Dialog.Close>
          </div>
          <form
            className="mt-6 space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              create.mutate();
            }}
          >
            <label className="block">
              <span className="mb-1.5 block font-mono text-[10px] uppercase tracking-[0.16em] text-muted">
                Title
              </span>
              <input
                autoFocus
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Backend Engineer - Stripe"
                className="focus-ring h-11 w-full rounded-field border border-line bg-paper px-3.5 text-sm"
              />
            </label>
            <div>
              <span className="mb-1.5 block font-mono text-[10px] uppercase tracking-[0.16em] text-muted">
                Editor
              </span>
              <div className="grid grid-cols-2 gap-1 rounded-field border border-line bg-paper p-1">
                {(["structured", "code"] as const).map((value) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => setMode(value)}
                    className={`rounded px-2 py-1.5 text-[12px] ${
                      mode === value ? "bg-ink text-paper" : "text-muted hover:text-ink"
                    }`}
                  >
                    {value === "structured" ? "Form editor" : "LaTeX editor"}
                  </button>
                ))}
              </div>
            </div>
            <label className="block">
              <span className="mb-1.5 block font-mono text-[10px] uppercase tracking-[0.16em] text-muted">
                {mode === "structured" ? "Template" : "Starting LaTeX template"}
              </span>
              <select
                value={templateId}
                onChange={(event) => setTemplateId(event.target.value)}
                className="focus-ring h-11 w-full rounded-field border border-line bg-paper px-3 text-sm"
              >
                {templates.map((template) => (
                  <option key={template.id} value={template.id}>
                    {template.name} {template.atsSafe ? "(ATS safe)" : ""}
                  </option>
                ))}
              </select>
            </label>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={create.isPending}>
                {create.isPending ? "Creating..." : "Create resume"}
              </Button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
