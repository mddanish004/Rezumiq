import { Eye, EyeOff } from "lucide-react";
import type { Basics } from "@/lib/resume";
import { LinksEditor, MiniField } from "./Fields";

export function BasicsEditor({
  basics,
  onChange,
}: {
  basics: Basics;
  onChange: (basics: Basics) => void;
}) {
  const sensitive = basics.sensitive ?? [];
  const toggleSensitive = (field: "name" | "location") => {
    const next = sensitive.includes(field)
      ? sensitive.filter((item) => item !== field)
      : [...sensitive, field];
    onChange({ ...basics, sensitive: next.length ? next : null });
  };

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="relative">
          <MiniField label="Full name" value={basics.name} onChange={(name) => onChange({ ...basics, name })} placeholder="Rohan Kulkarni" />
          <button
            type="button"
            onClick={() => toggleSensitive("name")}
            className="absolute right-1.5 top-0 grid h-6 w-6 place-items-center rounded text-muted/60 hover:bg-soft hover:text-ink"
            title={sensitive.includes("name") ? "Name is masked before AI requests" : "Mask name before AI requests"}
            aria-label="Toggle name masking"
          >
            {sensitive.includes("name") ? <EyeOff size={11} /> : <Eye size={11} />}
          </button>
        </div>
        <MiniField
          label="Professional title"
          value={basics.headline ?? ""}
          onChange={(headline) => onChange({ ...basics, headline })}
          placeholder="Staff Infrastructure Engineer"
        />
        <MiniField
          label="Email"
          type="email"
          value={basics.email ?? ""}
          onChange={(email) => onChange({ ...basics, email })}
          placeholder="you@example.com"
        />
        <MiniField
          label="Phone"
          value={basics.phone ?? ""}
          onChange={(phone) => onChange({ ...basics, phone })}
          placeholder="+91 98765 43210"
        />
        <div className="relative sm:col-span-2">
          <MiniField
            label="Location"
            value={basics.location ?? ""}
            onChange={(location) => onChange({ ...basics, location })}
            placeholder="Bengaluru, India"
          />
          <button
            type="button"
            onClick={() => toggleSensitive("location")}
            className="absolute right-1.5 top-0 grid h-6 w-6 place-items-center rounded text-muted/60 hover:bg-soft hover:text-ink"
            title={sensitive.includes("location") ? "Location is masked before AI requests" : "Mask location before AI requests"}
            aria-label="Toggle location masking"
          >
            {sensitive.includes("location") ? <EyeOff size={11} /> : <Eye size={11} />}
          </button>
        </div>
      </div>
      <div>
        <p className="mb-1 font-mono text-[9px] uppercase tracking-[0.12em] text-muted">Profile links</p>
        <LinksEditor links={basics.links} onChange={(links) => onChange({ ...basics, links })} />
      </div>
      <p className="text-[10px] leading-4 text-muted">
        Email and phone are always masked before an AI request. Name and location are masked when the eye is
        closed.
      </p>
    </div>
  );
}
