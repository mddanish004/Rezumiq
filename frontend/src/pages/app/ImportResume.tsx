import { useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Check, FileText, NotebookPen, Sparkles, Upload, Wand2 } from "lucide-react";
import { toast } from "sonner";
import { api, ApiError, uploadFile, type ImportResult, type Template } from "@/lib/api";
import { normalizeContent, wordCount } from "@/lib/resume";
import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ResumeDocument } from "@/components/resume/ResumeDocument";
import { cn } from "@/lib/utils";

type Mode = "upload" | "paste" | "notes";

const tabs: Array<{ id: Mode; label: string; icon: typeof Upload }> = [
  { id: "upload", label: "Upload a file", icon: Upload },
  { id: "paste", label: "Paste text", icon: FileText },
  { id: "notes", label: "Write from notes", icon: NotebookPen },
];

export default function ImportResume() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<Mode>("upload");
  const [result, setResult] = useState<ImportResult | null>(null);
  const [sourceName, setSourceName] = useState("");
  const [title, setTitle] = useState("");
  const [templateId, setTemplateId] = useState("developer");

  const templates = useQuery<Template[]>({ queryKey: ["templates"], queryFn: api.templates });
  const content = useMemo(
    () => (result ? normalizeContent(result.content) : null),
    [result],
  );

  const save = useMutation({
    mutationFn: () =>
      api.createResumeFromContent(title.trim() || sourceName || "Imported resume", content!, templateId),
    onSuccess: async (resume) => {
      await queryClient.invalidateQueries({ queryKey: ["resumes"] });
      await queryClient.invalidateQueries({ queryKey: ["usage"] });
      toast.success("Resume created from the import");
      navigate(`/app/resumes/${resume.id}/edit`);
    },
    onError: (error) => toast.error(error.message),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Workspace / Import"
        title="Bring a resume in."
        description="A PDF, LaTeX source, pasted text, or rough notes. The model extracts facts exactly as written; nothing is invented."
        actions={
          <Link to="/app/resumes" className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink">
            <ArrowLeft size={14} /> Resumes
          </Link>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
        <Card className="h-fit p-5">
          <div className="-mx-1 flex gap-1 overflow-x-auto border-b border-line px-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => {
                  setMode(tab.id);
                  setResult(null);
                }}
                className={cn(
                  "flex shrink-0 items-center gap-1.5 whitespace-nowrap border-b-2 px-2 py-2.5 text-[11px] transition-colors sm:px-2.5 sm:text-[12px]",
                  mode === tab.id
                    ? "border-ink font-medium text-ink"
                    : "border-transparent text-muted hover:text-ink",
                )}
              >
                <tab.icon size={13} /> {tab.label}
              </button>
            ))}
          </div>

          <div className="mt-5">
            {mode === "upload" ? (
              <UploadForm
                onImported={(data, name) => {
                  setResult(data);
                  setSourceName(name);
                  setTitle(name.replace(/\.[^.]+$/, "") || "Imported resume");
                }}
                onLatex={(resumeId) => navigate(`/app/resumes/${resumeId}/edit`)}
              />
            ) : null}
            {mode === "paste" ? (
              <PasteForm
                onImported={(data) => {
                  setResult(data);
                  setSourceName("Pasted resume");
                  setTitle("Imported resume");
                }}
              />
            ) : null}
            {mode === "notes" ? (
              <NotesForm
                onImported={(data, role) => {
                  setResult(data);
                  setSourceName(`${role} draft`);
                  setTitle(`${role} resume`);
                }}
              />
            ) : null}
          </div>
        </Card>

        <div className="min-w-0">
          {result && content ? (
            <div className="space-y-3">
              <Card className="p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">Ready to save</p>
                    <p className="mt-1 text-sm">
                      {content.sections.length} sections · {wordCount(content)} words
                    </p>
                  </div>
                  <Badge tone="success">
                    <Check size={11} /> Extracted
                  </Badge>
                </div>
                <div className="mt-3 grid gap-3 sm:grid-cols-[minmax(0,1fr)_180px]">
                  <label className="block">
                    <span className="mb-1 block font-mono text-[9px] uppercase tracking-[0.12em] text-muted">
                      Resume title
                    </span>
                    <input
                      value={title}
                      onChange={(event) => setTitle(event.target.value)}
                      className="focus-ring h-9 w-full rounded-field border border-line bg-paper px-2.5 text-[13px]"
                    />
                  </label>
                  <label className="block">
                    <span className="mb-1 block font-mono text-[9px] uppercase tracking-[0.12em] text-muted">
                      Template
                    </span>
                    <select
                      value={templateId}
                      onChange={(event) => setTemplateId(event.target.value)}
                      className="focus-ring h-9 w-full rounded-field border border-line bg-paper px-2 text-[12px]"
                    >
                      {(templates.data ?? []).map((template) => (
                        <option key={template.id} value={template.id}>
                          {template.name}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                {result.missed.length ? (
                  <div className="mt-3 rounded-field border border-warning/25 bg-warning/5 p-3">
                    <p className="text-[11px] font-medium text-warning">
                      {result.missed.length} line{result.missed.length === 1 ? "" : "s"} the reader could not place
                    </p>
                    <ul className="mt-1.5 space-y-0.5 text-[11px] leading-5 text-muted">
                      {result.missed.slice(0, 6).map((line, index) => (
                        <li key={index} className="truncate">
                          {line.placed ? "Kept as a hidden bullet: " : "Missed: "}
                          {line.text}
                        </li>
                      ))}
                    </ul>
                    <p className="mt-1.5 text-[10px] text-muted">
                      Nothing is lost. Open the editor to place missed lines yourself.
                    </p>
                  </div>
                ) : null}

                <div className="mt-4 flex flex-wrap items-center gap-2">
                  <Button onClick={() => save.mutate()} disabled={save.isPending}>
                    {save.isPending ? "Saving..." : "Save as a resume"}
                    {!save.isPending ? <ArrowRight size={14} /> : null}
                  </Button>
                  <Button variant="secondary" onClick={() => setResult(null)}>
                    Import another
                  </Button>
                </div>
              </Card>

              <div className="overflow-hidden rounded-card border border-line bg-white shadow-soft">
                <div className="flex items-center justify-between border-b border-line bg-surface px-3 py-2">
                  <span className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">
                    Import preview
                  </span>
                  <span className="font-mono text-[9px] text-muted">{sourceName}</span>
                </div>
                <div className="max-h-[70vh] overflow-auto bg-canvas p-3">
                  <div className="document-shadow mx-auto w-fit">
                    <ResumeDocument content={content} />
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="grid h-full min-h-[420px] place-items-center rounded-card border border-dashed border-line bg-surface/40 p-8">
              <div className="max-w-sm text-center">
                <span className="mx-auto grid h-12 w-12 place-items-center rounded-full border border-line bg-surface">
                  <Sparkles size={18} />
                </span>
                <p className="mt-3 font-display text-xl">The preview lands here</p>
                <p className="mt-1 text-sm leading-6 text-muted">
                  Import first, then check every line before it becomes a resume. The original file is never
                  published.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ErrorNote({ error }: { error: unknown }) {
  if (!error) return null;
  const isQuota = error instanceof ApiError && error.status === 402;
  const noKey = error instanceof ApiError && error.status === 503;
  return (
    <div className="rounded-field border border-danger/20 bg-danger/5 p-3 text-sm text-danger">
      <p>{error instanceof Error ? error.message : "That did not work"}</p>
      {isQuota ? (
        <Link
          to="/app/billing"
          className="mt-2 inline-flex items-center gap-1 text-xs font-medium underline decoration-danger/30 underline-offset-2"
        >
          Compare plans <ArrowRight size={12} />
        </Link>
      ) : null}
      {noKey ? (
        <Link
          to="/app/settings"
          className="mt-2 inline-flex items-center gap-1 text-xs font-medium underline decoration-danger/30 underline-offset-2"
        >
          Add an AI key <ArrowRight size={12} />
        </Link>
      ) : null}
    </div>
  );
}

function UploadForm({
  onImported,
  onLatex,
}: {
  onImported: (data: ImportResult, name: string) => void;
  onLatex: (resumeId: string) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [latexText, setLatexText] = useState("");

  const run = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error("Choose a file first");
      const uploaded = await uploadFile(file);
      return api.importResume({ uploadId: uploaded.id });
    },
    onSuccess: (data) => {
      toast.success("Resume read");
      onImported(data, file?.name ?? "Imported resume");
    },
    onError: (error) => toast.error(error.message),
  });

  const keepLatex = useMutation({
    mutationFn: () => api.createResumeFromTex(file!.name.replace(/\.[^.]+$/, "") || "LaTeX resume", latexText),
    onSuccess: (resume) => {
      toast.success("LaTeX resume created");
      onLatex(resume.id);
    },
    onError: (error) => toast.error(error.message),
  });

  const pick = async (next: File | null) => {
    setFile(next);
    setLatexText("");
    if (next && /\.tex$/i.test(next.name)) setLatexText(await next.text());
  };

  return (
    <div className="space-y-4">
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.tex,.txt,text/plain,application/pdf"
        className="sr-only"
        onChange={(event) => void pick(event.target.files?.[0] ?? null)}
      />
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="focus-ring flex w-full flex-col items-center gap-2 rounded-card border border-dashed border-line bg-paper/60 px-4 py-8 text-center transition-colors hover:border-ink/30"
      >
        <span className="grid h-10 w-10 place-items-center rounded-full border border-line bg-surface">
          <Upload size={16} />
        </span>
        <span className="text-sm font-medium">{file ? file.name : "Choose a PDF, .tex or .txt file"}</span>
        <span className="text-xs text-muted">
          {file ? `${Math.max(1, Math.round(file.size / 1024))} KB · click to change` : "Up to 5 MB. Text is read, never stored as a resume until you save."}
        </span>
      </button>

      <div className="flex flex-wrap gap-2">
        <Button onClick={() => run.mutate()} disabled={!file || run.isPending}>
          <Wand2 size={14} /> {run.isPending ? "Reading the file..." : "Read and convert"}
        </Button>
        {file && /\.tex$/i.test(file.name) ? (
          <Button variant="secondary" onClick={() => keepLatex.mutate()} disabled={keepLatex.isPending || !latexText}>
            Keep the LaTeX source
          </Button>
        ) : null}
      </div>

      <ErrorNote error={run.error ?? keepLatex.error} />
      <p className="text-[11px] leading-5 text-muted">
        PDFs are parsed as text and read back through the same parser the ATS check uses. LaTeX can stay LaTeX
        or become an editable form.
      </p>
    </div>
  );
}

function PasteForm({ onImported }: { onImported: (data: ImportResult) => void }) {
  const [text, setText] = useState("");
  const run = useMutation({
    mutationFn: () => api.importResume({ text: text.trim() }),
    onSuccess: (data) => {
      toast.success("Resume read");
      onImported(data);
    },
    onError: (error) => toast.error(error.message),
  });

  return (
    <div className="space-y-4">
      <label className="block">
        <span className="mb-1 block font-mono text-[9px] uppercase tracking-[0.12em] text-muted">
          Resume text
        </span>
        <textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          rows={12}
          placeholder="Paste the full resume here, including the header and every section."
          className="focus-ring w-full resize-y rounded-field border border-line bg-paper p-3 text-[13px] leading-6"
        />
        <span className="mt-1 block text-right font-mono text-[9px] text-muted">{text.length} chars</span>
      </label>
      <Button onClick={() => run.mutate()} disabled={text.trim().length < 20 || run.isPending}>
        <Wand2 size={14} /> {run.isPending ? "Reading..." : "Read and convert"}
      </Button>
      <ErrorNote error={run.error} />
    </div>
  );
}

function NotesForm({ onImported }: { onImported: (data: ImportResult, role: string) => void }) {
  const [role, setRole] = useState("");
  const [notes, setNotes] = useState("");
  const run = useMutation({
    mutationFn: () => api.draftResume(role.trim(), notes.trim()),
    onSuccess: (data) => {
      toast.success("Draft written from your notes");
      onImported(data, role.trim());
    },
    onError: (error) => toast.error(error.message),
  });

  return (
    <div className="space-y-4">
      <label className="block">
        <span className="mb-1 block font-mono text-[9px] uppercase tracking-[0.12em] text-muted">
          Target role
        </span>
        <input
          value={role}
          onChange={(event) => setRole(event.target.value)}
          placeholder="Backend Engineer"
          className="focus-ring h-9 w-full rounded-field border border-line bg-paper px-2.5 text-[13px]"
        />
      </label>
      <label className="block">
        <span className="mb-1 block font-mono text-[9px] uppercase tracking-[0.12em] text-muted">
          Rough notes
        </span>
        <textarea
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          rows={10}
          placeholder={
            "Worked at Acme 2023-2025 on the billing team. Cut checkout latency from 900ms to 220ms. Built the refunds service in Go. B.Tech CSE from BITS, 2023."
          }
          className="focus-ring w-full resize-y rounded-field border border-line bg-paper p-3 text-[13px] leading-6"
        />
      </label>
      <Button
        onClick={() => run.mutate()}
        disabled={role.trim().length < 2 || notes.trim().length < 40 || run.isPending}
      >
        <Sparkles size={14} /> {run.isPending ? "Writing the draft..." : "Write a draft"}
      </Button>
      <ErrorNote error={run.error} />
      <p className="text-[11px] leading-5 text-muted">
        Only facts from the notes. No metrics, employers or skills are invented. Review everything before
        saving.
      </p>
    </div>
  );
}
