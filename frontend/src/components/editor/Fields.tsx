import { useRef } from "react";
import { Bold, Eye, EyeOff, Link2, Plus, Trash2 } from "lucide-react";
import type { Bullet, Link } from "@/lib/resume";
import { emptyLink } from "@/lib/resume";
import { cn } from "@/lib/utils";

export const inputClass =
  "focus-ring h-9 w-full rounded-field border border-line bg-paper px-2.5 text-[13px] text-ink placeholder:text-muted/60";

function labelClass() {
  return "mb-1 block font-mono text-[9px] uppercase tracking-[0.12em] text-muted";
}

export function MiniField({
  label,
  value,
  onChange,
  placeholder,
  className,
  type = "text",
  list,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  type?: string;
  list?: string;
}) {
  return (
    <label className={cn("block", className)}>
      <span className={labelClass()}>{label}</span>
      <input
        type={type}
        list={list}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className={inputClass}
      />
    </label>
  );
}

export function DateField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <MiniField
      label={label}
      value={value}
      onChange={onChange}
      placeholder="YYYY-MM or present"
      list="date-suggestions"
    />
  );
}

export function HiddenToggle({
  hidden,
  onChange,
  noun = "item",
}: {
  hidden: boolean;
  onChange: (hidden: boolean) => void;
  noun?: string;
}) {
  return (
    <button
      type="button"
      onClick={() => onChange(!hidden)}
      className={cn(
        "focus-ring inline-flex h-7 items-center gap-1 rounded-field border px-2 font-mono text-[9px] uppercase tracking-[0.08em]",
        hidden ? "border-warning/30 bg-warning/10 text-warning" : "border-line bg-paper text-muted hover:text-ink",
      )}
      title={hidden ? `Show this ${noun}` : `Hide this ${noun} from the PDF`}
    >
      {hidden ? <EyeOff size={11} /> : <Eye size={11} />}
      {hidden ? "Hidden" : "Visible"}
    </button>
  );
}

export function BulletList({
  bullets,
  onChange,
}: {
  bullets: Bullet[];
  onChange: (bullets: Bullet[]) => void;
}) {
  const update = (bulletId: string, text: string) =>
    onChange(bullets.map((bullet) => (bullet.id === bulletId ? { ...bullet, text } : bullet)));
  const toggle = (bulletId: string) =>
    onChange(bullets.map((bullet) => (bullet.id === bulletId ? { ...bullet, hidden: !bullet.hidden } : bullet)));
  const remove = (bulletId: string) => onChange(bullets.filter((bullet) => bullet.id !== bulletId));

  return (
    <div className="space-y-1.5">
      {bullets.map((bullet) => (
        <BulletRow
          key={bullet.id}
          bullet={bullet}
          onChange={(text) => update(bullet.id, text)}
          onToggle={() => toggle(bullet.id)}
          onRemove={() => remove(bullet.id)}
        />
      ))}
      <button
        type="button"
        onClick={() => onChange([...bullets, { id: `b_${Math.random().toString(36).slice(2, 9)}`, text: "" }])}
        className="inline-flex items-center gap-1.5 rounded-field px-2 py-1.5 text-[12px] text-muted transition-colors hover:bg-soft hover:text-ink"
      >
        <Plus size={12} /> Add bullet
      </button>
    </div>
  );
}

function BulletRow({
  bullet,
  onChange,
  onToggle,
  onRemove,
}: {
  bullet: Bullet;
  onChange: (text: string) => void;
  onToggle: () => void;
  onRemove: () => void;
}) {
  const ref = useRef<HTMLTextAreaElement>(null);

  const wrap = (before: string, after: string) => {
    const element = ref.current;
    if (!element) return;
    const start = element.selectionStart;
    const end = element.selectionEnd;
    const selected = bullet.text.slice(start, end) || "text";
    const next = `${bullet.text.slice(0, start)}${before}${selected}${after}${bullet.text.slice(end)}`;
    onChange(next);
    requestAnimationFrame(() => {
      element.focus();
      element.setSelectionRange(start + before.length, start + before.length + selected.length);
    });
  };

  return (
    <div className={cn("group rounded-field border bg-paper/60 p-2", bullet.hidden ? "border-warning/20" : "border-line")}>
      <textarea
        ref={ref}
        value={bullet.text}
        rows={Math.max(2, Math.ceil(bullet.text.length / 78))}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Start with a strong verb. Say what you built and what changed."
        className="focus-ring w-full resize-none rounded bg-transparent px-0.5 py-0.5 text-[12px] leading-5 text-ink outline-none placeholder:text-muted/50"
      />
      <div className="flex items-center gap-0.5 opacity-70 transition-opacity group-hover:opacity-100">
        <button
          type="button"
          onClick={() => wrap("**", "**")}
          className="focus-ring grid h-6 w-6 place-items-center rounded text-muted hover:bg-soft hover:text-ink"
          aria-label="Bold selection"
          title="Bold"
        >
          <Bold size={11} />
        </button>
        <button
          type="button"
          onClick={() => {
            const url = window.prompt("Link address (https://...)");
            if (url) wrap("[", `](${url})`);
          }}
          className="focus-ring grid h-6 w-6 place-items-center rounded text-muted hover:bg-soft hover:text-ink"
          aria-label="Link selection"
          title="Inline link"
        >
          <Link2 size={11} />
        </button>
        <button
          type="button"
          onClick={onToggle}
          className="focus-ring grid h-6 w-6 place-items-center rounded text-muted hover:bg-soft hover:text-ink"
          aria-label={bullet.hidden ? "Show bullet" : "Hide bullet"}
          title={bullet.hidden ? "Show in PDF" : "Keep in editor, hide from PDF"}
        >
          {bullet.hidden ? <EyeOff size={11} /> : <Eye size={11} />}
        </button>
        <button
          type="button"
          onClick={onRemove}
          className="focus-ring ml-auto grid h-6 w-6 place-items-center rounded text-muted hover:bg-danger/5 hover:text-danger"
          aria-label="Remove bullet"
        >
          <Trash2 size={11} />
        </button>
      </div>
    </div>
  );
}

export function LinksEditor({
  links,
  onChange,
}: {
  links: Link[];
  onChange: (links: Link[]) => void;
}) {
  const update = (index: number, patch: Partial<Link>) =>
    onChange(links.map((link, position) => (position === index ? { ...link, ...patch } : link)));

  return (
    <div className="space-y-2">
      {links.map((link, index) => (
        <div key={`${index}-${link.label}`} className="grid grid-cols-[0.8fr_1.2fr_auto] items-end gap-2">
          <MiniField label="Label" value={link.label} onChange={(value) => update(index, { label: value })} placeholder="GitHub" />
          <MiniField label="URL" value={link.url} onChange={(value) => update(index, { url: value })} placeholder="https://..." />
          <button
            type="button"
            onClick={() => onChange(links.filter((_, position) => position !== index))}
            className="focus-ring mb-0.5 grid h-9 w-9 place-items-center rounded-field border border-line text-muted hover:border-danger/30 hover:text-danger"
            aria-label="Remove link"
          >
            <Trash2 size={13} />
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={() => onChange([...links, emptyLink()])}
        className="inline-flex items-center gap-1.5 rounded-field px-2 py-1.5 text-[12px] text-muted transition-colors hover:bg-soft hover:text-ink"
      >
        <Plus size={12} /> Add link
      </button>
    </div>
  );
}

export function CommaList({
  label,
  values,
  onChange,
  placeholder,
}: {
  label: string;
  values: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
}) {
  return (
    <label className="block">
      <span className={labelClass()}>{label}</span>
      <input
        value={values.join(", ")}
        onChange={(event) =>
          onChange(
            event.target.value
              .split(",")
              .map((value) => value.trim())
              .filter(Boolean),
          )
        }
        placeholder={placeholder ?? "Comma separated"}
        className={inputClass}
      />
    </label>
  );
}
