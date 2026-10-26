import type { ReactNode } from "react";
import type { Content, Entry, Layout, Section } from "@/lib/resume";
import { cn } from "@/lib/utils";

function formatMonth(value: string) {
  const trimmed = value.trim();
  if (!trimmed) return "";
  if (/^present$/i.test(trimmed)) return "Present";
  const match = /^(\d{4})-(\d{2})$/.exec(trimmed);
  if (!match) return trimmed;
  const date = new Date(Number(match[1]), Number(match[2]) - 1, 1);
  return new Intl.DateTimeFormat("en-IN", { month: "short", year: "numeric" }).format(date);
}

function dateRange(start?: string | null, end?: string | null) {
  const from = start ? formatMonth(start) : "";
  const to = end ? formatMonth(end) : "";
  if (from && to) return `${from} — ${to}`;
  return from || to;
}

export function RichText({ text }: { text: string }) {
  const tokens = text.split(/(\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))/g).filter(Boolean);
  return (
    <>
      {tokens.map((token, index) => {
        if (token.startsWith("**") && token.endsWith("**")) {
          return <strong key={index}>{token.slice(2, -2)}</strong>;
        }
        const link = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(token);
        if (link) {
          return (
            <a
              key={index}
              href={link[2]}
              target="_blank"
              rel="noreferrer"
              className="underline decoration-ink/25 underline-offset-2 hover:decoration-ink"
            >
              {link[1]}
            </a>
          );
        }
        return <span key={index}>{token}</span>;
      })}
    </>
  );
}

const spacingMap = {
  compact: { sections: "space-y-4", entries: "space-y-2.5", bullets: "space-y-0.5" },
  normal: { sections: "space-y-6", entries: "space-y-4", bullets: "space-y-1" },
  relaxed: { sections: "space-y-8", entries: "space-y-5", bullets: "space-y-1.5" },
} as const;

export function ResumeDocument({
  content,
  layout,
  className,
}: {
  content: Content;
  layout?: Layout | null;
  className?: string;
}) {
  const spacing = spacingMap[layout?.spacing ?? "normal"] ?? spacingMap.normal;
  const fontClass =
    layout?.fontSize === 10 ? "text-[11px]" : layout?.fontSize === 12 ? "text-[13px]" : "text-[12px]";

  const links = content.basics.links ?? [];

  return (
    <article
      className={cn(
        "mx-auto w-full max-w-[760px] bg-white px-8 py-10 text-ink sm:px-12 sm:py-12",
        fontClass,
        className,
      )}
    >
      <header className="border-b border-ink/15 pb-4">
        <h1 className="font-display text-[30px] leading-tight tracking-[-0.01em] sm:text-[34px]">
          {content.basics.name || "Your name"}
        </h1>
        {content.basics.headline ? (
          <p className="mt-1 text-[13px] text-muted">{content.basics.headline}</p>
        ) : null}
        <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-muted">
          {content.basics.email ? <span>{content.basics.email}</span> : null}
          {content.basics.phone ? <span>· {content.basics.phone}</span> : null}
          {content.basics.location ? <span>· {content.basics.location}</span> : null}
          {links.map((link) => (
            <span key={`${link.label}-${link.url}`}>
              ·{" "}
              <a
                href={link.url}
                target="_blank"
                rel="noreferrer"
                className="underline decoration-ink/20 underline-offset-2 hover:decoration-ink"
              >
                {link.label}
              </a>
            </span>
          ))}
        </div>
      </header>

      <div className={cn("mt-5", spacing.sections)}>
        {content.sections.filter((section) => !section.hidden).map((section) => (
          <DocumentSection key={section.id} section={section} spacing={spacing} />
        ))}
      </div>
    </article>
  );
}

function DocumentSection({
  section,
  spacing,
}: {
  section: Section;
  spacing: (typeof spacingMap)[keyof typeof spacingMap];
}) {
  if (section.type === "summary") {
    if (!section.text?.trim()) return null;
    return (
      <section>
        <SectionTitle>{section.title}</SectionTitle>
        <p className="mt-1.5 leading-[1.55] text-ink/90">
          <RichText text={section.text} />
        </p>
      </section>
    );
  }

  if (section.type === "skills") {
    const groups = (section.groups ?? []).filter((group) => group.name || group.items.length);
    if (!groups.length) return null;
    return (
      <section>
        <SectionTitle>{section.title}</SectionTitle>
        <div className="mt-1.5 space-y-1">
          {groups.map((group) => (
            <p key={group.id} className="leading-[1.5]">
              {group.name ? <strong className="font-semibold">{group.name}: </strong> : null}
              {group.items.join(", ")}
            </p>
          ))}
        </div>
      </section>
    );
  }

  if (section.type === "links") {
    const links = (section.links ?? []).filter((link) => link.label && link.url);
    if (!links.length) return null;
    return (
      <section>
        <SectionTitle>{section.title}</SectionTitle>
        <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-1">
          {links.map((link) => (
            <a
              key={`${link.label}-${link.url}`}
              href={link.url}
              target="_blank"
              rel="noreferrer"
              className="underline decoration-ink/25 underline-offset-2 hover:decoration-ink"
            >
              {link.label}
            </a>
          ))}
        </div>
      </section>
    );
  }

  const entries = (section.entries ?? []).filter((entry) => !entry.hidden);
  if (!entries.length) return null;

  return (
    <section>
      <SectionTitle>{section.title}</SectionTitle>
      <div className={cn("mt-2", spacing.entries)}>
        {entries.map((entry) => (
          <DocumentEntry
            key={entry.id}
            entry={entry}
            type={section.type}
            bulletGap={spacing.bullets}
          />
        ))}
      </div>
    </section>
  );
}

function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <h2 className="border-b border-ink/20 pb-1 font-mono text-[9px] font-medium uppercase tracking-[0.18em] text-ink/70">
      {children}
    </h2>
  );
}

function DocumentEntry({
  entry,
  type,
  bulletGap,
}: {
  entry: Entry;
  type: Section["type"];
  bulletGap: string;
}) {
  const bullets = (entry.bullets ?? []).filter((bullet) => !bullet.hidden && bullet.text.trim());
  const dates = dateRange(entry.start, entry.end);

  return (
    <div>
      <div className="flex items-baseline justify-between gap-4">
        <div className="min-w-0">
          {type === "experience" ? (
            <p className="leading-snug">
              <strong className="font-semibold">{entry.role || entry.organization}</strong>
              {entry.role && entry.organization ? <span> · {entry.organization}</span> : null}
            </p>
          ) : null}
          {type === "education" ? (
            <p className="leading-snug">
              <strong className="font-semibold">{entry.institution}</strong>
              {entry.degree || entry.field ? (
                <span>
                  {" "}
                  — {[entry.degree, entry.field].filter(Boolean).join(", ")}
                </span>
              ) : null}
              {entry.score ? <span className="text-muted"> · {entry.score}</span> : null}
            </p>
          ) : null}
          {type === "projects" ? (
            <p className="leading-snug">
              <strong className="font-semibold">
                {entry.url ? (
                  <a
                    href={entry.url}
                    target="_blank"
                    rel="noreferrer"
                    className="underline decoration-ink/25 underline-offset-2 hover:decoration-ink"
                  >
                    {entry.name}
                  </a>
                ) : (
                  entry.name
                )}
              </strong>
              {entry.technologies?.length ? (
                <span className="text-muted"> · {entry.technologies.join(", ")}</span>
              ) : null}
            </p>
          ) : null}
          {type === "list" ? (
            <p className="leading-snug">
              <strong className="font-semibold">{entry.title}</strong>
              {entry.subtitle ? <span> — {entry.subtitle}</span> : null}
            </p>
          ) : null}
          {entry.location ? <p className="text-[11px] text-muted">{entry.location}</p> : null}
        </div>
        {dates || entry.date ? (
          <p className="shrink-0 font-mono text-[10px] uppercase tracking-[0.06em] text-muted">
            {dates || entry.date}
          </p>
        ) : null}
      </div>

      {entry.links?.length ? (
        <p className="mt-1 flex flex-wrap gap-x-3 text-[11px]">
          {entry.links.map((link) => (
            <a
              key={`${link.label}-${link.url}`}
              href={link.url}
              target="_blank"
              rel="noreferrer"
              className="underline decoration-ink/25 underline-offset-2 hover:decoration-ink"
            >
              {link.label}
            </a>
          ))}
        </p>
      ) : null}

      {bullets.length ? (
        <ul className={cn("mt-1.5", bulletGap)}>
          {bullets.map((bullet) => (
            <li key={bullet.id} className="flex gap-2 leading-[1.5]">
              <span aria-hidden className="mt-[0.55em] h-[3px] w-[3px] shrink-0 rounded-full bg-ink/70" />
              <span>
                <RichText text={bullet.text} />
              </span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
