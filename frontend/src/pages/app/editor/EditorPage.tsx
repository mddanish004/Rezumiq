import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  ChevronDown,
  Code2,
  Download,
  Eye,
  Gauge,
  History,
  LayoutTemplate,
  Plus,
  Share2,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";
import { api, ApiError, previewPdf, type Job, type ResumeDetail, type Template } from "@/lib/api";
import type { Content, Layout, Section, SectionType, VersionDetail } from "@/lib/resume";
import { emptyContent, newSection, normalizeContent, sectionTitle, wordCount } from "@/lib/resume";
import { BasicsEditor } from "@/components/editor/BasicsEditor";
import { SectionEditor } from "@/components/editor/SectionEditor";
import { PreviewPane } from "@/components/editor/PreviewPane";
import { VersionDrawer } from "@/components/editor/VersionDrawer";
import { AiDrawer } from "@/components/editor/AiDrawer";
import { AtsDialog } from "@/components/editor/AtsDialog";
import { ShareDialog } from "@/components/share/ShareDialog";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { useMediaQuery } from "@/lib/useMediaQuery";
import { cn, formatRelative } from "@/lib/utils";

const SECTION_TYPES: SectionType[] = ["summary", "experience", "education", "projects", "skills", "links", "list"];

export default function EditorPage() {
  const { id = "" } = useParams();
  const resumeQuery = useQuery<ResumeDetail>({
    queryKey: ["resume", id],
    queryFn: () => api.resume(id),
    enabled: Boolean(id),
    staleTime: Infinity,
  });
  const templates = useQuery<Template[]>({ queryKey: ["templates"], queryFn: api.templates });
  const jobs = useQuery<Job[]>({ queryKey: ["jobs"], queryFn: api.jobs });

  if (resumeQuery.isLoading) {
    return (
      <div className="grid place-items-center py-24">
        <Spinner label="Opening the editor" />
      </div>
    );
  }
  if (resumeQuery.isError || !resumeQuery.data) {
    return (
      <div className="space-y-4">
        <Link to="/app/resumes" className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink">
          <ArrowLeft size={14} /> Back to resumes
        </Link>
        <p className="text-sm text-danger">That resume could not be loaded.</p>
      </div>
    );
  }

  const resume = resumeQuery.data;
  if (resume.mode === "code") {
    return <LatexEditor resume={resume} templates={templates.data ?? []} jobs={jobs.data ?? []} />;
  }
  return (
    <StructuredEditor
      resume={resume}
      templates={templates.data ?? []}
      jobs={jobs.data ?? []}
    />
  );
}

function StructuredEditor({
  resume,
  templates,
  jobs,
}: {
  resume: ResumeDetail;
  templates: Template[];
  jobs: Job[];
}) {
  const queryClient = useQueryClient();
  const [content, setContent] = useState<Content>((resume.head?.content as Content) ?? emptyContent());
  const [title, setTitle] = useState(resume.title);
  const [templateId, setTemplateId] = useState(resume.templateId ?? "developer");
  const [layout, setLayout] = useState<Layout>((resume.layout as Layout) ?? { spacing: "normal" });
  const [pageLimit, setPageLimit] = useState(resume.pageLimit);
  const [jobId, setJobId] = useState(resume.jobId ?? "");
  const [headVersionId, setHeadVersionId] = useState(resume.head?.id ?? null);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [conflict, setConflict] = useState(false);
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const [saveError, setSaveError] = useState("");
  const [layoutOpen, setLayoutOpen] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);
  const [aiOpen, setAiOpen] = useState(false);
  const [aiTarget, setAiTarget] = useState<{ ids: string[]; label: string } | null>(null);
  const [atsOpen, setAtsOpen] = useState(false);
  const [mobilePreview, setMobilePreview] = useState(false);
  const [latestAts, setLatestAts] = useState(resume.latestAts ?? null);
  const isDesktop = useMediaQuery("(min-width: 1280px)");

  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(true);
  const [previewError, setPreviewError] = useState("");
  const [pageCount, setPageCount] = useState(0);
  const previewObjectRef = useRef<string | null>(null);

  const savedRef = useRef({
    content: JSON.stringify(content),
    meta: JSON.stringify({ title, templateId, layout, pageLimit, jobId }),
  });
  const savingRef = useRef(false);

  const contentJson = useMemo(() => JSON.stringify(content), [content]);
  const metaJson = useMemo(
    () => JSON.stringify({ title, templateId, layout, pageLimit, jobId }),
    [title, templateId, layout, pageLimit, jobId],
  );

  const save = useCallback(
    async ({ label, silent = true }: { label?: string; silent?: boolean } = {}) => {
      if (savingRef.current || conflict) return;
      const normalized = normalizeContent(content);
      const normalizedJson = JSON.stringify(normalized);
      const metaChanged = metaJson !== savedRef.current.meta;
      const contentChanged = normalizedJson !== savedRef.current.content;
      if (!metaChanged && !contentChanged && !label) {
        setDirty(false);
        return;
      }

      savingRef.current = true;
      setSaving(true);
      setSaveError("");
      try {
        if (metaChanged) {
          await api.updateResume(resume.id, {
            title: title.trim() || "Untitled resume",
            templateId,
            pageLimit,
            layout,
            jobId: jobId || null,
          });
          savedRef.current.meta = metaJson;
        }
        if (contentChanged || label) {
          const version = await api.createVersion(resume.id, {
            kind: "manual",
            baseVersionId: headVersionId,
            content: normalized,
            label: label ?? null,
          });
          setHeadVersionId(version.id);
          savedRef.current.content = normalizedJson;
        }
        setDirty(JSON.stringify(normalizeContent(content)) !== savedRef.current.content);
        setSavedAt(new Date());
        void queryClient.invalidateQueries({ queryKey: ["resumes"] });
        void queryClient.invalidateQueries({ queryKey: ["usage"] });
        if (!silent) toast.success(label ? "Checkpoint saved" : "Saved");
      } catch (error) {
        if (error instanceof ApiError && error.status === 409) {
          setConflict(true);
          setSaveError("This resume was changed in another tab. Reload before saving again.");
        } else {
          setSaveError(error instanceof Error ? error.message : "Could not save");
          if (!silent) toast.error(error instanceof Error ? error.message : "Could not save");
        }
      } finally {
        savingRef.current = false;
        setSaving(false);
      }
    },
    [conflict, content, contentJson, headVersionId, jobId, layout, metaJson, pageLimit, queryClient, resume.id, templateId, title],
  );

  const ensureSaved = useCallback(async () => {
    if (savingRef.current) {
      await new Promise<void>((resolve) => {
        const timer = window.setInterval(() => {
          if (!savingRef.current) {
            window.clearInterval(timer);
            resolve();
          }
        }, 100);
      });
    }
    await save({ silent: true });
  }, [save]);

  useEffect(() => {
    if (conflict) return;
    const metaNow = JSON.stringify({ title, templateId, layout, pageLimit, jobId });
    const normalizedJson = JSON.stringify(normalizeContent(content));
    if (normalizedJson === savedRef.current.content && metaNow === savedRef.current.meta) {
      setDirty(false);
      return;
    }
    setDirty(true);
    const timer = window.setTimeout(() => void save(), 1100);
    return () => window.clearTimeout(timer);
  }, [contentJson, save, conflict, jobId, layout, pageLimit, templateId, title]);

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setPreviewLoading(true);
      setPreviewError("");
      try {
        const result = await previewPdf({ templateId, content: normalizeContent(content), layout }, controller.signal);
        if (previewObjectRef.current) URL.revokeObjectURL(previewObjectRef.current);
        const url = URL.createObjectURL(result.blob);
        previewObjectRef.current = url;
        setPreviewUrl(url);
        setPageCount(result.pageCount);
      } catch (error) {
        if ((error as Error).name === "AbortError") return;
        setPreviewError(error instanceof Error ? error.message : "Could not compile the preview");
      } finally {
        setPreviewLoading(false);
      }
    }, 1100);
    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [content, layout, templateId]);

  useEffect(() => () => {
    if (previewObjectRef.current) URL.revokeObjectURL(previewObjectRef.current);
  }, []);

  const updateSection = (next: Section) =>
    setContent((current) => ({
      ...current,
      sections: current.sections.map((section) => (section.id === next.id ? next : section)),
    }));

  const addSection = (type: SectionType) => {
    setContent((current) => ({ ...current, sections: [...current.sections, newSection(type)] }));
    setAddOpen(false);
  };

  const applyVersion = (version: VersionDetail) => {
    if (version.content) {
      setContent(version.content);
      savedRef.current.content = JSON.stringify(version.content);
    }
    setHeadVersionId(version.id);
    setDirty(false);
    setSavedAt(new Date());
    void queryClient.invalidateQueries({ queryKey: ["resume", resume.id] });
  };

  const saveState = conflict
    ? "Conflict"
    : saving
      ? "Saving..."
      : dirty
        ? "Unsaved changes"
        : savedAt
          ? `Saved ${formatRelative(savedAt.toISOString())}`
          : "All changes saved";

  return (
    <div className="space-y-0">
      <datalist id="date-suggestions">
        <option value="present" />
        <option value="2026" />
        <option value="2025" />
        <option value="2024" />
      </datalist>

      <div className="sticky top-0 z-20 -mx-4 border-b border-line bg-paper/95 px-4 py-3 backdrop-blur-md sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8">
        <div className="flex flex-wrap items-center gap-2">
          <Link to="/app/resumes" className="inline-flex items-center gap-1.5 text-xs text-muted hover:text-ink">
            <ArrowLeft size={13} /> Resumes
          </Link>
          <span className="hidden h-4 w-px bg-line sm:block" />
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            onBlur={() => void save()}
            className="focus-ring min-w-0 max-w-md flex-1 rounded px-1 py-0.5 font-display text-xl outline-none hover:bg-surface focus:bg-surface"
            aria-label="Resume title"
          />
          <span className={cn("rounded-full border px-2 py-1 font-mono text-[9px] uppercase tracking-[0.1em]", conflict ? "border-danger/30 bg-danger/5 text-danger" : "border-line bg-surface text-muted")}>
            {saveState}
          </span>
          <div className="ml-auto flex flex-wrap items-center gap-1.5">
            <Button size="sm" variant="ghost" className="lg:hidden" onClick={() => setMobilePreview(true)}>
              <Eye size={13} /> Preview
            </Button>
            <Button size="sm" variant="secondary" onClick={() => setHistoryOpen(true)}>
              <History size={13} /> History
            </Button>
            <Button size="sm" variant="secondary" onClick={() => setAtsOpen(true)}>
              <Gauge size={13} /> ATS
            </Button>
            <Button size="sm" variant="secondary" onClick={() => setShareOpen(true)}>
              <Share2 size={13} /> Share
            </Button>
            <Button
              size="sm"
              onClick={async () => {
                await ensureSaved();
                setAiTarget(null);
                setAiOpen(true);
              }}
            >
              <Sparkles size={13} /> Ask AI
            </Button>
            <Button
              size="sm"
              variant="ghost"
              title="Switch this resume to the LaTeX editor"
              onClick={async () => {
                await ensureSaved();
                await api.updateResume(resume.id, { mode: "code" });
                window.location.reload();
              }}
            >
              <Code2 size={13} /> LaTeX
            </Button>
            <a href={api.resumePdfUrl(resume.id)} target="_blank" rel="noreferrer">
              <Button size="sm" variant="dark">
                <Download size={13} /> PDF
              </Button>
            </a>
          </div>
        </div>

        <div className="mt-2 flex flex-wrap items-center gap-2">
          <label className="flex items-center gap-1.5 text-[11px] text-muted">
            <LayoutTemplate size={12} />
            <select
              value={templateId}
              onChange={(event) => setTemplateId(event.target.value)}
              className="focus-ring h-7 rounded border border-line bg-surface px-1.5 text-[11px] text-ink"
            >
              {templates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </select>
          </label>
          {templates.find((template) => template.id === templateId)?.atsSafe ? <Badge tone="success">ATS safe</Badge> : null}
          <label className="flex items-center gap-1.5 text-[11px] text-muted">
            Pages
            <select
              value={pageLimit}
              onChange={(event) => setPageLimit(Number(event.target.value))}
              className="focus-ring h-7 rounded border border-line bg-surface px-1.5 text-[11px] text-ink"
            >
              {[1, 2, 3].map((limit) => <option key={limit} value={limit}>{limit}</option>)}
            </select>
          </label>
          <label className="flex items-center gap-1.5 text-[11px] text-muted">
            Target
            <select
              value={jobId}
              onChange={(event) => setJobId(event.target.value)}
              className="focus-ring h-7 max-w-44 rounded border border-line bg-surface px-1.5 text-[11px] text-ink"
            >
              <option value="">No job</option>
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {[job.company, job.role].filter(Boolean).join(" · ") || "Saved posting"}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            onClick={() => setLayoutOpen((value) => !value)}
            className="focus-ring inline-flex h-7 items-center gap-1 rounded border border-line bg-surface px-2 text-[11px] text-muted hover:text-ink"
          >
            Layout <ChevronDown size={11} />
          </button>
          {latestAts ? <Badge tone="success">ATS {latestAts.score}</Badge> : null}
          <span className="ml-auto font-mono text-[10px] uppercase tracking-[0.1em] text-muted">
            {wordCount(content)} words · limit {pageLimit}p · {pageCount || "..."} compiled
          </span>
        </div>

        {layoutOpen ? (
          <div className="mt-2 grid gap-3 rounded-field border border-line bg-surface p-3 sm:grid-cols-3">
            <label className="text-[11px] text-muted">
              Spacing
              <select
                value={layout.spacing}
                onChange={(event) => setLayout({ ...layout, spacing: event.target.value as Layout["spacing"] })}
                className="focus-ring mt-1 h-8 w-full rounded border border-line bg-paper px-2 text-[12px] text-ink"
              >
                <option value="compact">Compact</option>
                <option value="normal">Normal</option>
                <option value="relaxed">Relaxed</option>
              </select>
            </label>
            <label className="text-[11px] text-muted">
              Font size
              <select
                value={layout.fontSize ?? ""}
                onChange={(event) => setLayout({ ...layout, fontSize: event.target.value ? (Number(event.target.value) as 10 | 11 | 12) : null })}
                className="focus-ring mt-1 h-8 w-full rounded border border-line bg-paper px-2 text-[12px] text-ink"
              >
                <option value="">Template default</option>
                <option value="10">10 pt</option>
                <option value="11">11 pt</option>
                <option value="12">12 pt</option>
              </select>
            </label>
            <label className="text-[11px] text-muted">
              Header links
              <select
                value={layout.links ?? ""}
                onChange={(event) => setLayout({ ...layout, links: (event.target.value || null) as Layout["links"] })}
                className="focus-ring mt-1 h-8 w-full rounded border border-line bg-paper px-2 text-[12px] text-ink"
              >
                <option value="">Template default</option>
                <option value="icon-and-link">Icon + address</option>
                <option value="icon-and-name">Icon + name</option>
                <option value="link">Address only</option>
              </select>
            </label>
          </div>
        ) : null}

        {conflict ? (
          <div className="mt-2 flex flex-wrap items-center justify-between gap-2 rounded-field border border-danger/20 bg-danger/5 px-3 py-2 text-xs text-danger">
            <span>This resume was saved in another tab. Reload to get the latest version.</span>
            <Button size="sm" variant="secondary" onClick={() => window.location.reload()}>
              Reload
            </Button>
          </div>
        ) : null}
        {saveError && !conflict ? (
          <p className="mt-2 text-xs text-danger">{saveError}</p>
        ) : null}
      </div>

      <div className="grid gap-5 pt-5 xl:grid-cols-[minmax(0,1fr)_minmax(0,0.92fr)]">
        <div className="space-y-4">
          <section className="rounded-card border border-line bg-surface p-4 shadow-soft">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">Basics / contact</p>
                <h2 className="font-display text-xl">Who is this resume for?</h2>
              </div>
              <Badge tone="outline">PII masked</Badge>
            </div>
            <BasicsEditor basics={content.basics} onChange={(basics) => setContent({ ...content, basics })} />
          </section>

          {content.sections.map((section, index) => (
            <SectionEditor
              key={section.id}
              section={section}
              index={index}
              count={content.sections.length}
              onChange={updateSection}
              onDelete={() => {
                if (window.confirm(`Delete the ${section.title} section?`)) {
                  setContent((current) => ({ ...current, sections: current.sections.filter((item) => item.id !== section.id) }));
                }
              }}
              onMove={(direction) => {
                const next = [...content.sections];
                const target = index + direction;
                if (target < 0 || target >= next.length) return;
                [next[index], next[target]] = [next[target], next[index]];
                setContent({ ...content, sections: next });
              }}
              onAskAi={async (target) => {
                await ensureSaved();
                setAiTarget({ ids: [target.id], label: target.title });
                setAiOpen(true);
              }}
            />
          ))}

          <div className="relative">
            <button
              type="button"
              onClick={() => setAddOpen((value) => !value)}
              className="flex w-full items-center justify-center gap-1.5 rounded-card border border-dashed border-line bg-surface/50 py-3 text-[13px] text-muted transition-colors hover:border-ink/30 hover:text-ink"
            >
              <Plus size={14} /> Add a section
            </button>
            {addOpen ? (
              <>
                <button
                  type="button"
                  className="fixed inset-0 z-10 cursor-default"
                  aria-label="Close section menu"
                  onClick={() => setAddOpen(false)}
                />
                <div className="absolute inset-x-0 bottom-full z-20 mb-2 grid grid-cols-2 gap-1 rounded-card border border-line bg-surface p-2 shadow-lift sm:grid-cols-4">
                  {SECTION_TYPES.map((type) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => addSection(type)}
                      className="rounded-field px-2 py-2 text-left text-[12px] text-muted hover:bg-soft hover:text-ink"
                    >
                      {sectionTitle(type)}
                    </button>
                  ))}
                </div>
              </>
            ) : null}
          </div>

          <div className="flex flex-wrap items-center justify-between gap-2 rounded-card border border-line bg-surface px-4 py-3">
            <div>
              <p className="text-[12px] font-medium">Done for now?</p>
              <p className="text-[11px] text-muted">Autosave keeps the head current. Name a checkpoint when you want a marker.</p>
            </div>
            <div className="flex gap-2">
              <Button size="sm" variant="secondary" onClick={() => void save({ silent: false })} disabled={saving}>
                Save now
              </Button>
              <Button size="sm" variant="secondary" onClick={() => setHistoryOpen(true)}>
                Checkpoints
              </Button>
            </div>
          </div>
        </div>

        {isDesktop ? (
          <div className="min-h-0">
            <div className="sticky top-[132px] h-[calc(100vh-150px)]">
              <PreviewPane
                url={previewUrl}
                loading={previewLoading}
                error={previewError}
                pageCount={pageCount}
                onDownload={() => window.open(api.resumePdfUrl(resume.id), "_blank", "noopener")}
                className="h-full"
              />
            </div>
          </div>
        ) : null}
      </div>

      {mobilePreview ? (
        <div className="fixed inset-0 z-50 flex flex-col bg-paper p-3 xl:hidden">
          <div className="mb-2 flex items-center justify-between">
            <p className="font-display text-lg">Preview</p>
            <Button size="sm" variant="secondary" onClick={() => setMobilePreview(false)}>
              Close
            </Button>
          </div>
          <PreviewPane
            url={previewUrl}
            loading={previewLoading}
            error={previewError}
            pageCount={pageCount}
            onDownload={() => window.open(api.resumePdfUrl(resume.id), "_blank", "noopener")}
            className="min-h-0 flex-1"
          />
        </div>
      ) : null}

      <ShareDialog
        open={shareOpen}
        onOpenChange={setShareOpen}
        resumeId={resume.id}
        resumeTitle={resume.title}
      />

      <VersionDrawer
        open={historyOpen}
        onOpenChange={setHistoryOpen}
        resumeId={resume.id}
        headVersionId={headVersionId}
        onRestored={applyVersion}
        onCheckpoint={async (label) => {
          await save({ label, silent: false });
        }}
        saving={saving}
      />

      <AiDrawer
        open={aiOpen}
        onOpenChange={setAiOpen}
        resumeId={resume.id}
        content={content}
        jobs={jobs}
        initialTargetIds={aiTarget?.ids}
        targetLabel={aiTarget?.label}
        onApplied={applyVersion}
      />

      <AtsDialog
        open={atsOpen}
        onOpenChange={setAtsOpen}
        resumeId={resume.id}
        jobs={jobs}
        beforeRun={ensureSaved}
        onChecked={(report) => {
          setLatestAts({ score: report.score, grade: report.grade, jobId: jobId || null, checkedAt: new Date().toISOString() });
          void queryClient.invalidateQueries({ queryKey: ["resumes"] });
        }}
      />
    </div>
  );
}

function LatexEditor({ resume, jobs }: { resume: ResumeDetail; templates: Template[]; jobs: Job[] }) {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState(resume.title);
  const [tex, setTex] = useState(resume.head?.texSource ?? "");
  const [headVersionId, setHeadVersionId] = useState(resume.head?.id ?? null);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(true);
  const [previewError, setPreviewError] = useState("");
  const [pageCount, setPageCount] = useState(0);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);
  const [aiOpen, setAiOpen] = useState(false);
  const previewObjectRef = useRef<string | null>(null);
  const savedTex = useRef(resume.head?.texSource ?? "");

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setPreviewLoading(true);
      setPreviewError("");
      try {
        const result = await previewPdf({ texSource: tex }, controller.signal);
        if (previewObjectRef.current) URL.revokeObjectURL(previewObjectRef.current);
        const url = URL.createObjectURL(result.blob);
        previewObjectRef.current = url;
        setPreviewUrl(url);
        setPageCount(result.pageCount);
      } catch (error) {
        if ((error as Error).name === "AbortError") return;
        setPreviewError(error instanceof Error ? error.message : "Compile failed");
      } finally {
        setPreviewLoading(false);
      }
    }, 1100);
    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [tex]);

  useEffect(() => () => {
    if (previewObjectRef.current) URL.revokeObjectURL(previewObjectRef.current);
  }, []);

  const save = async (label?: string) => {
    if (saving) return;
    if (tex === savedTex.current && title === resume.title && !label) return;
    setSaving(true);
    try {
      if (title !== resume.title) await api.updateResume(resume.id, { title });
      if (tex !== savedTex.current || label) {
        const version = await api.createVersion(resume.id, {
          kind: "manual",
          baseVersionId: headVersionId,
          texSource: tex,
          label: label ?? null,
        });
        setHeadVersionId(version.id);
        savedTex.current = tex;
      }
      setSavedAt(new Date());
      void queryClient.invalidateQueries({ queryKey: ["resumes"] });
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not save");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2 border-b border-line pb-4">
        <Link to="/app/resumes" className="inline-flex items-center gap-1.5 text-xs text-muted hover:text-ink">
          <ArrowLeft size={13} /> Resumes
        </Link>
        <input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          className="focus-ring min-w-0 flex-1 rounded px-1 py-0.5 font-display text-xl outline-none hover:bg-surface focus:bg-surface"
        />
        <Badge tone="dark">LaTeX</Badge>
        <span className="font-mono text-[9px] uppercase tracking-[0.1em] text-muted">
          {saving ? "Saving..." : savedAt ? `Saved ${formatRelative(savedAt.toISOString())}` : "Compile as you type"}
        </span>
        <Button size="sm" variant="secondary" onClick={() => void save()} disabled={saving}>
          Save
        </Button>
        <Button size="sm" variant="secondary" onClick={() => setHistoryOpen(true)}>
          <History size={13} /> History
        </Button>
        <Button size="sm" onClick={() => setAiOpen(true)}>
          <Sparkles size={13} /> Fix compile
        </Button>
        <a href={api.resumePdfUrl(resume.id)} target="_blank" rel="noreferrer">
          <Button size="sm" variant="dark">
            <Download size={13} /> PDF
          </Button>
        </a>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <div className="overflow-hidden rounded-card border border-line bg-ink text-paper">
          <div className="flex items-center justify-between border-b border-paper/10 px-3 py-2 font-mono text-[9px] uppercase tracking-[0.12em] text-paper/50">
            <span>resume.tex</span>
            <span>{tex.split("\n").length} lines</span>
          </div>
          <textarea
            value={tex}
            onChange={(event) => setTex(event.target.value)}
            onBlur={() => void save()}
            spellCheck={false}
            className="h-[calc(100vh-220px)] w-full resize-none bg-transparent p-4 font-mono text-[12px] leading-6 text-paper outline-none"
          />
        </div>
        <PreviewPane
          url={previewUrl}
          loading={previewLoading}
          error={previewError}
          pageCount={pageCount}
          onDownload={() => window.open(api.resumePdfUrl(resume.id), "_blank", "noopener")}
          className="min-h-[620px]"
        />
      </div>
      <ShareDialog
        open={shareOpen}
        onOpenChange={setShareOpen}
        resumeId={resume.id}
        resumeTitle={resume.title}
      />

      <VersionDrawer
        open={historyOpen}
        onOpenChange={setHistoryOpen}
        resumeId={resume.id}
        headVersionId={headVersionId}
        onRestored={() => window.location.reload()}
        onCheckpoint={async (label) => {
          await save(label);
        }}
        saving={saving}
      />
      <AiDrawer
        open={aiOpen}
        onOpenChange={setAiOpen}
        resumeId={resume.id}
        content={emptyContent()}
        jobs={jobs}
        codeMode
        onApplied={(version) => {
          if (version.texSource) {
            setTex(version.texSource);
            savedTex.current = version.texSource;
            setHeadVersionId(version.id);
          }
          setAiOpen(false);
        }}
      />
    </div>
  );
}
