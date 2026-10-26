import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Plus, Save, UserRound, Wand2 } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { Content, Section, SectionType } from "@/lib/resume";
import { newSection, normalizeContent, sectionTitle, wordCount } from "@/lib/resume";
import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { BasicsEditor } from "@/components/editor/BasicsEditor";
import { SectionEditor } from "@/components/editor/SectionEditor";
import { ResumeDocument } from "@/components/resume/ResumeDocument";
import { cn, formatRelative } from "@/lib/utils";

const SECTION_TYPES: SectionType[] = ["summary", "experience", "education", "projects", "skills", "links", "list"];

export default function Profile() {
  const profile = useQuery({ queryKey: ["profile"], queryFn: api.profile });
  const [content, setContent] = useState<Content | null>(null);
  const [savedJson, setSavedJson] = useState("");
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const savingRef = useRef(false);

  useEffect(() => {
    if (!profile.data || content) return;
    const initial = normalizeContent(profile.data.content as Content);
    setContent(initial);
    setSavedJson(JSON.stringify(initial));
    setSavedAt(profile.data.updatedAt);
  }, [profile.data, content]);

  const normalized = useMemo(() => (content ? normalizeContent(content) : null), [content]);
  const normalizedJson = normalized ? JSON.stringify(normalized) : "";
  const dirty = Boolean(normalizedJson && normalizedJson !== savedJson);

  const save = useMutation({
    mutationFn: (value: Content) => api.saveProfile(value),
    onSuccess: (data) => {
      setSavedJson(JSON.stringify(normalizeContent(data.content as Content)));
      setSavedAt(data.updatedAt ?? new Date().toISOString());
    },
  });

  const saveRef = useRef(save);
  saveRef.current = save;

  useEffect(() => {
    if (!normalized || !dirty || savingRef.current) return;
    const timer = window.setTimeout(async () => {
      savingRef.current = true;
      try {
        await saveRef.current.mutateAsync(normalized);
      } catch (error) {
        toast.error(error instanceof Error ? error.message : "Could not save the profile");
      } finally {
        savingRef.current = false;
      }
    }, 1200);
    return () => window.clearTimeout(timer);
  }, [normalized, normalizedJson, dirty, save.isPending]);

  if (profile.isError) {
    return (
      <Card className="p-6 text-sm text-danger">
        The profile could not be loaded. Refresh the page, or check that the API is running.
      </Card>
    );
  }

  if (profile.isLoading || !content) {
    return (
      <div className="grid place-items-center py-24">
        <Spinner label="Opening the profile" />
      </div>
    );
  }

  const updateSection = (next: Section) =>
    setContent((current) =>
      current
        ? { ...current, sections: current.sections.map((section) => (section.id === next.id ? next : section)) }
        : current,
    );

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Workspace / Profile"
        title="The master profile."
        description="Every AI action reads this. Keep the full history here, then trim per resume. Email and phone are always masked before a request."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={dirty ? "warning" : "success"}>
              {save.isPending ? "Saving" : dirty ? "Unsaved changes" : savedAt ? `Saved ${formatRelative(savedAt)}` : "Saved"}
            </Badge>
            <Button size="sm" variant="secondary" onClick={() => save.mutate(normalized!)} disabled={!dirty || save.isPending}>
              <Save size={13} /> Save now
            </Button>
          </div>
        }
      />

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(0,0.85fr)]">
        <div className="space-y-4">
          <Card className="p-4">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">Basics / contact</p>
                <h2 className="font-display text-xl">Who you are</h2>
              </div>
              <Badge tone="outline">
                <UserRound size={10} /> Source of truth
              </Badge>
            </div>
            <BasicsEditor basics={content.basics} onChange={(basics) => setContent({ ...content, basics })} />
          </Card>

          {content.sections.map((section, index) => (
            <SectionEditor
              key={section.id}
              section={section}
              index={index}
              count={content.sections.length}
              onChange={updateSection}
              onDelete={() => {
                if (window.confirm(`Remove the ${section.title} section from the profile?`)) {
                  setContent({ ...content, sections: content.sections.filter((item) => item.id !== section.id) });
                }
              }}
              onMove={(direction) => {
                const next = [...content.sections];
                const target = index + direction;
                if (target < 0 || target >= next.length) return;
                [next[index], next[target]] = [next[target], next[index]];
                setContent({ ...content, sections: next });
              }}
              onAskAi={() => {
                toast.info("Tailor or edit a resume to change its wording. The profile keeps the facts.");
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
                      onClick={() => {
                        setContent({ ...content, sections: [...content.sections, newSection(type)] });
                        setAddOpen(false);
                      }}
                      className="rounded-field px-2 py-2 text-left text-[12px] text-muted hover:bg-soft hover:text-ink"
                    >
                      {sectionTitle(type)}
                    </button>
                  ))}
                </div>
              </>
            ) : null}
          </div>

          <Card className="flex flex-wrap items-center justify-between gap-3 p-4">
            <div>
              <p className="text-[12px] font-medium">{wordCount(content)} words in the profile</p>
              <p className="text-[11px] text-muted">
                Resumes never inherit text automatically. Include a fact here once, then add it where it fits.
              </p>
            </div>
            <Link to="/app/import">
              <Button size="sm" variant="secondary">
                <Wand2 size={13} /> Import into a resume
              </Button>
            </Link>
          </Card>
        </div>

        <div className="hidden xl:block">
          <div className="sticky top-[92px] h-[calc(100vh-120px)] overflow-hidden rounded-card border border-line bg-canvas">
            <div className="flex items-center justify-between border-b border-line bg-surface px-3 py-2">
              <span className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">Profile sheet</span>
              <span className="font-mono text-[9px] text-muted">{content.sections.length} {content.sections.length === 1 ? "section" : "sections"}</span>
            </div>
            <div className="h-[calc(100%-38px)] overflow-auto p-3">
              <div className={cn("document-shadow mx-auto w-fit", save.isPending && "opacity-90")}>
                <ResumeDocument content={content} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
