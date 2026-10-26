import {
  ArrowDown,
  ArrowUp,
  ChevronDown,
  GripVertical,
  Plus,
  Sparkles,
  Trash2,
} from "lucide-react";
import { useState } from "react";
import type { Entry, Section } from "@/lib/resume";
import { newEntry } from "@/lib/resume";
import { BulletList, CommaList, DateField, HiddenToggle, LinksEditor, MiniField } from "./Fields";
import { cn } from "@/lib/utils";

export function SectionEditor({
  section,
  index,
  count,
  onChange,
  onDelete,
  onMove,
  onAskAi,
}: {
  section: Section;
  index: number;
  count: number;
  onChange: (section: Section) => void;
  onDelete: () => void;
  onMove: (direction: -1 | 1) => void;
  onAskAi: (section: Section) => void;
}) {
  const [open, setOpen] = useState(true);

  const updateEntry = (entryId: string, patch: Partial<Entry>) =>
    onChange({
      ...section,
      entries: (section.entries ?? []).map((entry) => (entry.id === entryId ? { ...entry, ...patch } : entry)),
    });
  const removeEntry = (entryId: string) =>
    onChange({ ...section, entries: (section.entries ?? []).filter((entry) => entry.id !== entryId) });
  const addEntry = () => onChange({ ...section, entries: [...(section.entries ?? []), newEntry(section)] });

  return (
    <section className="rounded-card border border-line bg-surface shadow-soft">
      <header className="flex flex-wrap items-center gap-2 border-b border-line px-4 py-3">
        <GripVertical size={14} className="hidden text-line sm:block" />
        <span className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">{section.type}</span>
        <input
          value={section.title}
          onChange={(event) => onChange({ ...section, title: event.target.value })}
          className="focus-ring min-w-0 flex-1 rounded px-1 py-0.5 font-display text-lg outline-none hover:bg-paper focus:bg-paper"
          aria-label="Section title"
        />
        <div className="flex items-center gap-1">
          <HiddenToggle hidden={Boolean(section.hidden)} onChange={(hidden) => onChange({ ...section, hidden })} noun="section" />
          <button
            type="button"
            onClick={() => onAskAi(section)}
            className="focus-ring grid h-7 w-7 place-items-center rounded-field border border-line bg-paper text-muted hover:text-ink"
            title="Ask AI about this section"
            aria-label="Ask AI about this section"
          >
            <Sparkles size={12} />
          </button>
          <button
            type="button"
            onClick={() => onMove(-1)}
            disabled={index === 0}
            className="focus-ring grid h-7 w-7 place-items-center rounded-field text-muted hover:bg-soft hover:text-ink disabled:opacity-30"
            aria-label="Move section up"
          >
            <ArrowUp size={12} />
          </button>
          <button
            type="button"
            onClick={() => onMove(1)}
            disabled={index === count - 1}
            className="focus-ring grid h-7 w-7 place-items-center rounded-field text-muted hover:bg-soft hover:text-ink disabled:opacity-30"
            aria-label="Move section down"
          >
            <ArrowDown size={12} />
          </button>
          <button
            type="button"
            onClick={onDelete}
            className="focus-ring grid h-7 w-7 place-items-center rounded-field text-muted hover:bg-danger/5 hover:text-danger"
            aria-label="Delete section"
          >
            <Trash2 size={12} />
          </button>
          <button
            type="button"
            onClick={() => setOpen((value) => !value)}
            className="focus-ring grid h-7 w-7 place-items-center rounded-field text-muted hover:bg-soft hover:text-ink"
            aria-label={open ? "Collapse section" : "Expand section"}
          >
            <ChevronDown size={13} className={cn("transition-transform", !open && "-rotate-90")} />
          </button>
        </div>
      </header>

      {open ? (
        <div className="space-y-4 p-4">
          {section.type === "summary" ? (
            <textarea
              value={section.text ?? ""}
              onChange={(event) => onChange({ ...section, text: event.target.value })}
              rows={3}
              placeholder="Two sentences on what you do and the scale you do it at."
              className="focus-ring w-full resize-y rounded-field border border-line bg-paper p-3 text-[13px] leading-6 outline-none"
            />
          ) : null}

          {section.type === "skills" ? (
            <div className="space-y-2">
              {(section.groups ?? []).map((group) => (
                <div key={group.id} className="grid grid-cols-[0.6fr_1.4fr_auto] items-end gap-2 rounded-field border border-line bg-paper/50 p-2">
                  <MiniField
                    label="Group"
                    value={group.name}
                    onChange={(name) =>
                      onChange({
                        ...section,
                        groups: (section.groups ?? []).map((item) => (item.id === group.id ? { ...item, name } : item)),
                      })
                    }
                    placeholder="Languages"
                  />
                  <CommaList
                    label="Items"
                    values={group.items}
                    onChange={(items) =>
                      onChange({
                        ...section,
                        groups: (section.groups ?? []).map((item) => (item.id === group.id ? { ...item, items } : item)),
                      })
                    }
                    placeholder="Go, Python, Postgres"
                  />
                  <button
                    type="button"
                    onClick={() => onChange({ ...section, groups: (section.groups ?? []).filter((item) => item.id !== group.id) })}
                    className="focus-ring mb-0.5 grid h-9 w-9 place-items-center rounded-field border border-line text-muted hover:border-danger/30 hover:text-danger"
                    aria-label="Remove skill group"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={() =>
                  onChange({
                    ...section,
                    groups: [...(section.groups ?? []), { id: `g_${Math.random().toString(36).slice(2, 9)}`, name: "", items: [] }],
                  })
                }
                className="inline-flex items-center gap-1.5 rounded-field px-2 py-1 text-[12px] text-muted hover:bg-soft hover:text-ink"
              >
                <Plus size={12} /> Add group
              </button>
            </div>
          ) : null}

          {section.type === "links" ? (
            <LinksEditor links={section.links ?? []} onChange={(links) => onChange({ ...section, links })} />
          ) : null}

          {["experience", "education", "projects", "list"].includes(section.type) ? (
            <div className="space-y-3">
              {(section.entries ?? []).map((entry) => (
                <EntryEditor
                  key={entry.id}
                  section={section}
                  entry={entry}
                  onChange={(patch) => updateEntry(entry.id, patch)}
                  onDelete={() => removeEntry(entry.id)}
                />
              ))}
              <button
                type="button"
                onClick={addEntry}
                className="inline-flex items-center gap-1.5 rounded-field border border-dashed border-line px-2.5 py-1.5 text-[12px] text-muted hover:border-ink/30 hover:text-ink"
              >
                <Plus size={12} /> Add {section.type === "experience" ? "role" : section.type === "education" ? "education" : section.type === "projects" ? "project" : "item"}
              </button>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function EntryEditor({
  section,
  entry,
  onChange,
  onDelete,
}: {
  section: Section;
  entry: Entry;
  onChange: (patch: Partial<Entry>) => void;
  onDelete: () => void;
}) {
  const heading =
    entry.organization || entry.institution || entry.name || entry.title || entry.role || "New entry";

  return (
    <div className="rounded-field border border-line bg-paper/40 p-3">
      <div className="flex items-center gap-2">
        <p className="min-w-0 flex-1 truncate text-[12px] font-medium">
          {heading || <span className="text-muted">New entry</span>}
          {entry.role && section.type === "experience" ? <span className="text-muted"> · {entry.role}</span> : null}
        </p>
        <HiddenToggle hidden={Boolean(entry.hidden)} onChange={(hidden) => onChange({ hidden })} noun="entry" />
        <button
          type="button"
          onClick={onDelete}
          className="focus-ring grid h-7 w-7 place-items-center rounded-field text-muted hover:bg-danger/5 hover:text-danger"
          aria-label="Delete entry"
        >
          <Trash2 size={12} />
        </button>
      </div>

      <div className="mt-3 grid gap-2.5 sm:grid-cols-2">
        {section.type === "experience" ? (
          <>
            <MiniField label="Organization" value={entry.organization ?? ""} onChange={(organization) => onChange({ organization })} placeholder="Razorpay" />
            <MiniField label="Role" value={entry.role ?? ""} onChange={(role) => onChange({ role })} placeholder="Systems Architect" />
          </>
        ) : null}
        {section.type === "education" ? (
          <>
            <MiniField label="Institution" value={entry.institution ?? ""} onChange={(institution) => onChange({ institution })} placeholder="BITS Pilani" />
            <MiniField label="Degree" value={entry.degree ?? ""} onChange={(degree) => onChange({ degree })} placeholder="B.E. Computer Science" />
            <MiniField label="Field" value={entry.field ?? ""} onChange={(field) => onChange({ field })} placeholder="Computer Science" />
            <MiniField label="Score" value={entry.score ?? ""} onChange={(score) => onChange({ score })} placeholder="8.9 / 10" />
          </>
        ) : null}
        {section.type === "projects" ? (
          <>
            <MiniField label="Project" value={entry.name ?? ""} onChange={(name) => onChange({ name })} placeholder="LedgerLite" />
            <MiniField label="URL" value={entry.url ?? ""} onChange={(url) => onChange({ url })} placeholder="https://github.com/..." />
            <div className="sm:col-span-2">
              <CommaList
                label="Technologies"
                values={entry.technologies ?? []}
                onChange={(technologies) => onChange({ technologies })}
                placeholder="Go, Kafka, Postgres"
              />
            </div>
          </>
        ) : null}
        {section.type === "list" ? (
          <>
            <MiniField label="Title" value={entry.title ?? ""} onChange={(title) => onChange({ title })} placeholder="Winner, Smart India Hackathon" />
            <MiniField label="Subtitle" value={entry.subtitle ?? ""} onChange={(subtitle) => onChange({ subtitle })} placeholder="Optional description" />
            <MiniField label="Date" value={entry.date ?? ""} onChange={(date) => onChange({ date })} placeholder="2025" />
            <MiniField label="URL" value={entry.url ?? ""} onChange={(url) => onChange({ url })} placeholder="https://..." />
          </>
        ) : null}
        {section.type === "experience" || section.type === "education" ? (
          <MiniField label="Location" value={entry.location ?? ""} onChange={(location) => onChange({ location })} placeholder="Bengaluru, India" />
        ) : null}
        {section.type !== "list" ? (
          <>
            <DateField label="Start" value={entry.start ?? ""} onChange={(start) => onChange({ start })} />
            <DateField label="End" value={entry.end ?? ""} onChange={(end) => onChange({ end })} />
          </>
        ) : null}
      </div>

      {section.type === "projects" ? (
        <div className="mt-3">
          <p className="mb-1 font-mono text-[9px] uppercase tracking-[0.12em] text-muted">Extra links</p>
          <LinksEditor links={entry.links ?? []} onChange={(links) => onChange({ links })} />
        </div>
      ) : null}

      <div className="mt-3 border-t border-line/70 pt-2.5">
        <p className="mb-1.5 font-mono text-[9px] uppercase tracking-[0.12em] text-muted">Bullets</p>
        <BulletList bullets={entry.bullets ?? []} onChange={(bullets) => onChange({ bullets })} />
      </div>
    </div>
  );
}
