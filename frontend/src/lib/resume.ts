export type Bullet = { id: string; text: string; hidden?: boolean };

export type Link = { label: string; url: string; sensitive?: boolean | null };

export type Entry = {
  id: string;
  hidden?: boolean;
  spaceAfter?: number | null;
  bullets: Bullet[];
  organization?: string;
  sensitive?: boolean | null;
  role?: string;
  location?: string | null;
  start?: string | null;
  end?: string | null;
  institution?: string;
  degree?: string | null;
  field?: string | null;
  score?: string | null;
  name?: string;
  url?: string | null;
  links?: Link[];
  technologies?: string[];
  title?: string;
  subtitle?: string | null;
  date?: string | null;
};

export type SkillGroup = { id: string; name: string; items: string[] };

export type SectionType = "summary" | "experience" | "education" | "projects" | "skills" | "links" | "list";

export type Section = {
  id: string;
  type: SectionType;
  title: string;
  hidden?: boolean;
  spaceAfter?: number | null;
  text?: string;
  entries?: Entry[];
  groups?: SkillGroup[];
  links?: Link[];
};

export type Basics = {
  name: string;
  headline?: string | null;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  links: Link[];
  sensitive?: Array<"name" | "location"> | null;
};

export type Content = { basics: Basics; sections: Section[] };

export type Layout = {
  spacing: "compact" | "normal" | "relaxed";
  fontSize?: 10 | 11 | 12 | null;
  links?: "icon-and-link" | "icon-and-name" | "link" | null;
};

export type Version = {
  id: string;
  parentId: string | null;
  kind: "import" | "manual" | "ai" | "restore" | "named";
  label: string | null;
  semver: string | null;
  createdAt: string;
};

export type VersionDetail = Version & {
  content: Content | null;
  texSource: string | null;
};

export function id(prefix = "x") {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

export function emptyContent(): Content {
  return { basics: { name: "", links: [] }, sections: [] };
}

export function newSection(type: SectionType): Section {
  const base = { id: id("s"), type, title: sectionTitle(type), hidden: false };
  if (type === "summary") return { ...base, text: "" };
  if (type === "skills") return { ...base, groups: [{ id: id("g"), name: "", items: [] }] };
  if (type === "links") return { ...base, links: [] };
  return { ...base, entries: [] };
}

export function sectionTitle(type: SectionType) {
  return (
    {
      summary: "Summary",
      experience: "Experience",
      education: "Education",
      projects: "Projects",
      skills: "Skills",
      links: "Links",
      list: "Achievements",
    } as const
  )[type];
}

export function newEntry(section: Section): Entry {
  if (section.type === "education") {
    return { id: id("e"), hidden: false, institution: "", bullets: [] };
  }
  if (section.type === "projects") {
    return { id: id("e"), hidden: false, name: "", bullets: [], links: [], technologies: [] };
  }
  if (section.type === "experience") {
    return { id: id("e"), hidden: false, organization: "", role: "", bullets: [] };
  }
  return { id: id("e"), hidden: false, title: "", bullets: [] };
}

export function newBullet(): Bullet {
  return { id: id("b"), text: "" };
}

export function wordCount(content: Content) {
  const parts: string[] = [
    content.basics.name,
    content.basics.headline ?? "",
    ...content.sections.flatMap((section) => {
      if (section.type === "summary") return [section.text ?? ""];
      if (section.type === "skills") return (section.groups ?? []).flatMap((group) => [group.name, ...group.items]);
      if (section.type === "links") return (section.links ?? []).map((link) => link.label);
      return (section.entries ?? []).flatMap((entry) => [
        entry.organization ?? "",
        entry.role ?? "",
        entry.institution ?? "",
        entry.degree ?? "",
        entry.field ?? "",
        entry.name ?? "",
        entry.title ?? "",
        entry.subtitle ?? "",
        ...(entry.bullets ?? []).map((bullet) => bullet.text),
      ]);
    }),
  ];
  return parts.join(" ").split(/\s+/).filter(Boolean).length;
}

export function bulletText(content: Content, bulletId: string) {
  for (const section of content.sections) {
    for (const entry of section.entries ?? []) {
      const bullet = (entry.bullets ?? []).find((item) => item.id === bulletId);
      if (bullet) return bullet.text;
    }
  }
  return "";
}

export function sectionById(content: Content, sectionId: string) {
  return content.sections.find((section) => section.id === sectionId);
}

export function emptyLink(): Link {
  return { label: "", url: "" };
}

function dateOrNull(value?: string | null) {
  const trimmed = (value ?? "").trim().toLowerCase();
  if (!trimmed) return null;
  return trimmed;
}

function normalizeUrl(value: string) {
  const trimmed = value.trim();
  if (!trimmed) return "";
  if (/^(https?:\/\/|mailto:)/i.test(trimmed)) return trimmed;
  return `https://${trimmed}`;
}

function normalizeLinks(links: Link[] | undefined): Link[] {
  return (links ?? [])
    .map((link) => ({
      label: link.label.trim(),
      url: normalizeUrl(link.url),
      ...(link.sensitive ? { sensitive: true } : {}),
    }))
    .filter((link) => link.label && link.url)
    .slice(0, 10);
}

function clip(value: string | null | undefined, max: number) {
  const trimmed = (value ?? "").trim();
  return trimmed ? trimmed.slice(0, max) : null;
}

export function normalizeContent(input: Content): Content {
  const basics: Basics = {
    name: input.basics.name.trim().slice(0, 100),
    headline: clip(input.basics.headline, 200),
    email: clip(input.basics.email, 254),
    phone: clip(input.basics.phone, 30),
    location: clip(input.basics.location, 200),
    links: normalizeLinks(input.basics.links),
    sensitive: input.basics.sensitive?.length ? input.basics.sensitive : null,
  };

  const sections = input.sections.map((section) => {
    const base = {
      id: section.id,
      type: section.type,
      title: (section.title.trim() || sectionTitle(section.type)).slice(0, 60),
      hidden: Boolean(section.hidden),
    };
    if (section.type === "summary") {
      return { ...base, text: (section.text ?? "").trim() };
    }
    if (section.type === "skills") {
      return {
        ...base,
        groups: (section.groups ?? [])
          .map((group) => ({
            id: group.id,
            name: group.name.trim().slice(0, 60),
            items: group.items.map((item) => item.trim().slice(0, 60)).filter(Boolean).slice(0, 40),
          }))
          .filter((group) => group.name && group.items.length)
          .slice(0, 15),
      };
    }
    if (section.type === "links") {
      return { ...base, links: normalizeLinks(section.links).slice(0, 15) };
    }
    return {
      ...base,
      entries: (section.entries ?? [])
        .slice(0, section.type === "education" ? 10 : section.type === "list" ? 40 : 30)
        .map((entry) => ({
          ...entry,
          organization: clip(entry.organization, 200) ?? "",
          role: clip(entry.role, 200) ?? "",
          institution: clip(entry.institution, 200) ?? "",
          degree: clip(entry.degree, 200),
          field: clip(entry.field, 200),
          score: clip(entry.score, 20),
          name: clip(entry.name, 200) ?? "",
          title: clip(entry.title, 400) ?? "",
          subtitle: clip(entry.subtitle, 400),
          location: clip(entry.location, 200),
          url: entry.url ? normalizeUrl(entry.url) : null,
          date: clip(entry.date, 40),
          start: dateOrNull(entry.start),
          end: dateOrNull(entry.end),
          technologies: (entry.technologies ?? []).map((item) => item.trim().slice(0, 40)).filter(Boolean).slice(0, 20),
          links: entry.links?.length ? normalizeLinks(entry.links).slice(0, 5) : undefined,
          bullets: (entry.bullets ?? [])
            .map((bullet) => ({ ...bullet, text: bullet.text.trim().slice(0, 1000) }))
            .filter((bullet) => bullet.text)
            .slice(0, 20),
        })),
    };
  });

  return { basics, sections: sections.slice(0, 20) } as Content;
}
