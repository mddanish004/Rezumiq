import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronDown,
  Code2,
  PenLine,
  Sparkles,
  Target,
} from "lucide-react";
import { PublicHeader } from "@/components/public/PublicHeader";
import { PublicFooter } from "@/components/public/PublicFooter";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export default function Landing() {
  return (
    <div className="min-h-screen bg-paper">
      <div className="border-b border-ink/10 bg-lime/70">
        <div className="mx-auto flex max-w-[1240px] flex-wrap items-center justify-center gap-x-3 gap-y-1 px-5 py-2 text-center font-mono text-[10px] uppercase tracking-[0.14em] text-ink">
          <span className="font-semibold">Season Pass</span>
          <span className="hidden h-3 w-px bg-ink/30 sm:block" />
          <span>Six months of AI for ₹499</span>
          <span className="hidden h-3 w-px bg-ink/30 sm:block" />
          <span className="text-ink/70">No auto-renew</span>
        </div>
      </div>

      <PublicHeader />

      <main>
        <section className="relative overflow-hidden">
          <div className="pointer-events-none absolute inset-x-0 top-0 h-[520px] paper-grid opacity-60" />
          <div className="relative mx-auto max-w-[1240px] px-5 pb-16 pt-14 lg:px-8 lg:pb-24 lg:pt-20">
            <div className="mx-auto max-w-3xl text-center">
              <div className="inline-flex items-center gap-2 rounded-full border border-line bg-surface/70 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.16em] text-muted">
                <span className="h-1.5 w-1.5 rounded-full bg-forest" />
                Editorial resume studio
                <span className="h-3 w-px bg-line" />
                Real LaTeX PDFs
              </div>
              <h1 className="mt-7 font-display text-[46px] leading-[0.98] tracking-[-0.035em] text-ink sm:text-[64px] lg:text-[76px]">
                Write with precision.
                <br />
                <span className="italic text-muted">Score with rigor.</span>
              </h1>
              <p className="mx-auto mt-6 max-w-xl text-[15px] leading-7 text-muted">
                A quiet, powerful resume builder for engineers, analysts, bankers, designers, and
                researchers. Import, tailor, score against real ATS parsers, and export a LaTeX PDF that
                looks like it took a weekend.
              </p>
              <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
                <Link to="/signup">
                  <Button size="lg" className="min-w-44">
                    Build my resume <ArrowRight size={16} />
                  </Button>
                </Link>
                <Link to="/ats-checker">
                  <Button size="lg" variant="secondary" className="min-w-44">
                    Check my ATS score
                  </Button>
                </Link>
              </div>
              <p className="mt-5 flex flex-wrap items-center justify-center gap-x-4 gap-y-1 font-mono text-[10px] uppercase tracking-[0.12em] text-muted">
                <span>Free tier</span>
                <span className="h-3 w-px bg-line" />
                <span>One AI-written resume</span>
                <span className="h-3 w-px bg-line" />
                <span>No card required</span>
              </p>
            </div>

            <EditorMock />
          </div>
        </section>

        <section id="features" className="border-t border-line bg-surface/40">
          <div className="mx-auto max-w-[1240px] px-5 py-16 lg:px-8 lg:py-24">
            <div className="max-w-2xl">
              <p className="eyebrow">Built like a studio, not a generator</p>
              <h2 className="mt-3 font-display text-3xl leading-tight tracking-[-0.02em] sm:text-4xl">
                Built for professionals who care about the <span className="italic">microscopic details.</span>
              </h2>
              <p className="mt-4 max-w-xl text-sm leading-7 text-muted">
                Two editors, real version history, and a scoring engine that tells you exactly what a
                parser saw, not a vague grade.
              </p>
            </div>
            <div className="mt-10 grid gap-4 md:grid-cols-3">
              <FeatureCard
                icon={<PenLine size={18} />}
                title="Draft authentically"
                description="Write in a structured form or in LaTeX. The form keeps the facts; the LaTeX keeps the craft."
                visual={<FormVisual />}
                action="Start with a form"
                to="/signup"
              />
              <FeatureCard
                icon={<Code2 size={18} />}
                title="LaTeX, imported"
                description="Bring a .tex file, a PDF, or plain text. The reader repairs structure and keeps your wording."
                visual={<CodeVisual />}
                action="Import a resume"
                to="/signup"
              />
              <FeatureCard
                icon={<Target size={18} />}
                title="Job-post tailoring"
                description="Paste a posting or a URL. Every suggested change is shown for review before it touches the page."
                visual={<TailorVisual />}
                action="Tailor to a role"
                to="/signup"
              />
            </div>
          </div>
        </section>

        <section className="border-t border-line bg-paper">
          <div className="mx-auto grid max-w-[1240px] items-center gap-10 px-5 py-16 lg:grid-cols-[1.05fr_0.95fr] lg:px-8 lg:py-24">
            <div>
              <Badge tone="lime" className="px-3 py-1 text-[9px]">
                The black-box problem
              </Badge>
              <h2 className="mt-5 font-display text-3xl leading-tight tracking-[-0.02em] sm:text-4xl">
                No black boxes.
                <br />
                <span className="italic text-muted">Audited against real ATS parsers.</span>
              </h2>
              <p className="mt-5 max-w-lg text-sm leading-7 text-muted">
                Most tools guess. Rezumiq compiles your PDF, reads it back through a parser like the ones
                recruiters use, and shows you every check that passed or failed.
              </p>
              <ul className="mt-7 space-y-3">
                {[
                  ["Zero invented keywords", "Facts come from your resume and profile, never from the model."],
                  ["Actionable fixes", "Every warning names the line and tells you what to do next."],
                  ["Knockout clarity", "See requirements the posting treats as mandatory, and what evidence is missing."],
                ].map(([title, body]) => (
                  <li key={title} className="flex gap-3">
                    <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full border border-line bg-surface">
                      <Check size={12} strokeWidth={2.5} />
                    </span>
                    <div>
                      <p className="text-sm font-medium text-ink">{title}</p>
                      <p className="text-sm leading-6 text-muted">{body}</p>
                    </div>
                  </li>
                ))}
              </ul>
              <Link to="/ats-checker" className="mt-7 inline-flex items-center gap-2 text-sm font-medium underline decoration-line underline-offset-4 hover:decoration-ink">
                Read a full score report <ArrowRight size={14} />
              </Link>
            </div>
            <ScoreCard />
          </div>
        </section>

        <section id="templates" className="border-t border-line bg-surface/40">
          <div className="mx-auto max-w-[1240px] px-5 py-16 lg:px-8 lg:py-24">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="eyebrow">Curated templates</p>
                <h2 className="mt-3 font-display text-3xl leading-tight tracking-[-0.02em] sm:text-4xl">
                  Engineered for recruiters who skim in <span className="italic">6 seconds.</span>
                </h2>
              </div>
              <Link to="/signup" className="text-sm font-medium underline decoration-line underline-offset-4 hover:decoration-ink">
                View all 14 templates
              </Link>
            </div>
            <div className="mt-9 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
              {TEMPLATES.map((template) => (
                <TemplateCard key={template.name} {...template} />
              ))}
            </div>
          </div>
        </section>

        <section className="border-t border-line bg-paper">
          <div className="mx-auto max-w-[1240px] px-5 py-16 lg:px-8 lg:py-24">
            <div className="text-center">
              <Badge tone="lime" className="px-3 py-1 text-[9px]">
                Four deliberate steps
              </Badge>
              <h2 className="mt-5 font-display text-3xl tracking-[-0.02em] sm:text-4xl">
                From first note to a verified draft.
              </h2>
              <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-muted">
                No dashboard tourist loop. Every step ends with something you can send.
              </p>
            </div>
            <div className="mt-10 grid gap-px overflow-hidden rounded-card border border-line bg-line sm:grid-cols-2 lg:grid-cols-4">
              {[
                ["01", "Start", "Blank, a template, or your master profile. Pick the shape and keep moving."],
                ["02", "Import or draft", "Drop a PDF, LaTeX, or notes. AI extracts facts and leaves the invented ones out."],
                ["03", "Tailor and score", "Review every AI change. Run the ATS report. Fix the exact lines that fail."],
                ["04", "Export and share", "Download a LaTeX PDF, keep versions, and watch how the link travels."],
              ].map(([number, title, body]) => (
                <div key={number} className="bg-surface p-6">
                  <p className="font-mono text-[11px] text-muted">{number}</p>
                  <h3 className="mt-4 font-display text-xl">{title}</h3>
                  <p className="mt-2 text-sm leading-6 text-muted">{body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <PricingSection />

        <section className="border-t border-line bg-paper">
          <div className="mx-auto grid max-w-[1240px] gap-10 px-5 py-16 lg:grid-cols-[0.8fr_1.2fr] lg:px-8 lg:py-24">
            <div>
              <p className="eyebrow">Before you pay</p>
              <h2 className="mt-3 font-display text-3xl tracking-[-0.02em] sm:text-4xl">
                Frequently considered questions.
              </h2>
              <p className="mt-4 text-sm leading-7 text-muted">
                If something is still unclear, the honest answer is usually in the docs, not a sales call.
              </p>
            </div>
            <div className="divide-y divide-line border-y border-line">
              {FAQS.map(([question, answer]) => (
                <details key={question} className="group py-5">
                  <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-sm font-medium text-ink">
                    {question}
                    <ChevronDown size={16} className="shrink-0 text-muted transition-transform group-open:rotate-180" />
                  </summary>
                  <p className="mt-3 max-w-2xl text-sm leading-7 text-muted">{answer}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-paper px-5 pb-16 lg:px-8">
          <div className="relative mx-auto max-w-[1240px] overflow-hidden rounded-[20px] bg-ink px-6 py-14 text-paper sm:px-12 lg:py-20">
            <div className="pointer-events-none absolute inset-0 opacity-20 paper-grid" />
            <div className="relative max-w-2xl">
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-paper/50">Your move</p>
              <h2 className="mt-4 font-display text-4xl leading-tight tracking-[-0.03em] sm:text-5xl">
                Ready to publish your <span className="italic text-lime">career story?</span>
              </h2>
              <p className="mt-4 max-w-lg text-sm leading-7 text-paper/65">
                Start free. Write one resume with AI, run the ATS report, and see whether the story reads
                the way you meant it.
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Link to="/signup">
                  <Button size="lg" className="min-w-40">
                    Start building for free
                  </Button>
                </Link>
                <Link to="/#pricing">
                  <Button size="lg" variant="secondary" className="min-w-40 border-paper/20 bg-transparent text-paper hover:bg-paper/10">
                    See pricing
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>

      <PublicFooter />
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
  visual,
  action,
  to,
}: {
  icon: ReactNode;
  title: string;
  description: string;
  visual: ReactNode;
  action: string;
  to: string;
}) {
  return (
    <article className="flex flex-col rounded-card border border-line bg-surface p-5">
      <div className="grid h-9 w-9 place-items-center rounded-full border border-line bg-paper text-ink">
        {icon}
      </div>
      <h3 className="mt-4 text-[15px] font-semibold">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-muted">{description}</p>
      <div className="mt-5">{visual}</div>
      <Link to={to} className="mt-5 inline-flex items-center gap-1.5 text-[13px] font-medium">
        {action} <ArrowUpRight size={13} />
      </Link>
    </article>
  );
}

function FormVisual() {
  return (
    <div className="rounded-lg border border-line bg-paper/70 p-3">
      <div className="flex items-center gap-2">
        <span className="rounded bg-ink px-1.5 py-0.5 font-mono text-[8px] uppercase tracking-wider text-paper">
          form
        </span>
        <span className="font-mono text-[9px] text-muted">BASICS / CONTACT</span>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2">
        {["ROHAN KULKARNI", "Staff Infrastructure", "rohan@hey.com", "Bengaluru, IN"].map((value, index) => (
          <div key={value} className={index > 1 ? "col-span-2" : ""}>
            <div className="h-1 w-8 rounded bg-line" />
            <div className="mt-1 truncate rounded border border-line bg-surface px-2 py-1.5 font-mono text-[8px]">
              {value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CodeVisual() {
  const lines = [
    ["\\documentclass", "{article}"],
    ["\\name", "{Rohan Kulkarni}"],
    ["\\section", "{Experience}"],
    ["  \\item", "Billing API in Go"],
    ["  \\item", "Cut p99 to 24ms"],
  ];
  return (
    <div className="rounded-lg border border-ink/70 bg-ink p-3 text-paper">
      <div className="flex items-center gap-1.5">
        <span className="h-2 w-2 rounded-full bg-paper/20" />
        <span className="h-2 w-2 rounded-full bg-paper/20" />
        <span className="h-2 w-2 rounded-full bg-lime" />
        <span className="ml-auto font-mono text-[8px] text-paper/40">resume.tex</span>
      </div>
      <div className="mt-2.5 space-y-1">
        {lines.map(([command, value], index) => (
          <p key={index} className="font-mono text-[8px] leading-4">
            <span className="text-paper/35">{String(index + 1).padStart(2, "0")}</span>{" "}
            <span className="text-lime">{command}</span>
            <span className="text-paper/70">{value}</span>
          </p>
        ))}
      </div>
    </div>
  );
}

function TailorVisual() {
  return (
    <div className="space-y-2 rounded-lg border border-line bg-paper/70 p-3">
      <div className="flex items-center justify-between font-mono text-[9px] text-muted">
        <span>STRIPE / STAFF ENG</span>
        <Badge tone="success">96% match</Badge>
      </div>
      <div className="rounded border border-line bg-surface p-2">
        <p className="font-mono text-[8px] text-muted">BEFORE</p>
        <p className="mt-1 text-[10px] leading-4 text-muted line-through decoration-danger/40">
          Worked on backend systems and APIs.
        </p>
      </div>
      <div className="rounded border border-forest/20 bg-forest/5 p-2">
        <p className="font-mono text-[8px] text-forest">AFTER</p>
        <p className="mt-1 text-[10px] leading-4 text-ink">
          Built a distributed billing ledger handling <strong>14M+ daily events</strong> at 99.9% uptime.
        </p>
      </div>
    </div>
  );
}

function ScoreCard() {
  return (
    <div className="rounded-card border border-line bg-surface p-5 shadow-soft">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted">ATS Audit / Stripe</p>
          <p className="mt-3 font-display text-2xl">Staff Platform Eng</p>
        </div>
        <div className="rounded-lg bg-lime px-3 py-2 text-center">
          <p className="font-display text-2xl leading-none">94</p>
          <p className="mt-0.5 font-mono text-[8px] uppercase tracking-[0.12em]">excellent</p>
        </div>
      </div>
      <div className="mt-5 space-y-2.5">
        {[
          ["Standard single-column", "pass"],
          ["Contact details found", "pass"],
          ["Section headings", "pass"],
          ["Action verbs", "pass"],
          ["Quantified results", "warn"],
        ].map(([label, state]) => (
          <div key={label} className="flex items-center justify-between border-b border-line/70 pb-2 text-xs last:border-0">
            <span className="flex items-center gap-2 text-ink">
              <span
                className={`grid h-4 w-4 place-items-center rounded-full ${
                  state === "pass" ? "bg-forest/10 text-forest" : "bg-warning/10 text-warning"
                }`}
              >
                {state === "pass" ? <Check size={10} strokeWidth={3} /> : <span className="text-[9px]">!</span>}
              </span>
              {label}
            </span>
            <span className="font-mono text-[9px] uppercase tracking-[0.1em] text-muted">{state}</span>
          </div>
        ))}
      </div>
      <div className="mt-4 flex flex-wrap gap-1.5">
        {["Go", "PostgreSQL", "Kafka", "AWS", "Terraform"].map((skill) => (
          <span key={skill} className="rounded-full border border-line bg-paper px-2 py-1 font-mono text-[9px] text-muted">
            {skill}
          </span>
        ))}
        <span className="rounded-full border border-warning/20 bg-warning/10 px-2 py-1 font-mono text-[9px] text-warning">
          + Kubernetes
        </span>
      </div>
      <div className="mt-5 flex items-center justify-between rounded-lg bg-ink px-3 py-2.5 text-paper">
        <span className="font-mono text-[9px] uppercase tracking-[0.12em] text-paper/60">
          Top fix / Impact
        </span>
        <span className="flex items-center gap-1 text-[11px] font-medium">
          Add scale to 2 bullets <ArrowRight size={12} />
        </span>
      </div>
    </div>
  );
}

const TEMPLATES = [
  { name: "Developer", field: "Tech", a: true },
  { name: "Jake's Resume", field: "Tech", a: true },
  { name: "Compact", field: "Tech", a: true },
  { name: "Modern", field: "Business", a: true },
  { name: "Analyst", field: "Business", a: true },
  { name: "Executive", field: "Leadership", a: false },
];

function TemplateCard({ name, field, a }: { name: string; field: string; a: boolean }) {
  return (
    <div className="group">
      <div className="overflow-hidden rounded-lg border border-line bg-surface p-2 transition-transform duration-200 group-hover:-translate-y-1">
        <div className="aspect-[3/4] rounded border border-line bg-paper p-2">
          <div className="mx-auto h-1.5 w-10 rounded bg-ink/70" />
          <div className="mx-auto mt-1 h-0.5 w-14 rounded bg-line" />
          <div className="mt-3 space-y-1">
            {[8, 6, 9, 5, 8, 4, 7].map((width, index) => (
              <div key={index} className="h-0.5 rounded bg-line" style={{ width: `${width * 8}%` }} />
            ))}
          </div>
          <div className="mt-3 space-y-1">
            <div className="h-0.5 w-6 rounded bg-forest/50" />
            {[9, 7, 8].map((width, index) => (
              <div key={index} className="h-0.5 rounded bg-line" style={{ width: `${width * 8}%` }} />
            ))}
          </div>
        </div>
      </div>
      <p className="mt-2.5 text-[12px] font-medium">{name}</p>
      <div className="mt-1 flex items-center justify-between">
        <span className="font-mono text-[9px] uppercase tracking-[0.1em] text-muted">{field}</span>
        <Badge tone={a ? "success" : "neutral"}>{a ? "ATS safe" : "Editorial"}</Badge>
      </div>
    </div>
  );
}

function PricingSection() {
  const plans = [
    {
      name: "Free",
      price: "₹0",
      cadence: "forever",
      description: "A real draft, not a demo.",
      features: ["1 AI-written resume", "1 AI tailor per month", "50 AI edits", "20 ATS checks", "LaTeX export"],
      cta: "Start free",
      highlighted: false,
    },
    {
      name: "Season Pass",
      price: "₹499",
      cadence: "one-time / 6 months",
      description: "For one focused season of applications.",
      features: ["40 AI tailors", "1,000 AI edits", "30 AI drafts", "200 ATS checks", "100 AI reviews"],
      cta: "Choose Season Pass",
      highlighted: true,
    },
    {
      name: "Pro",
      price: "₹129",
      cadence: "per month",
      description: "For a career that keeps moving.",
      features: ["60 AI tailors", "1,000 AI edits", "30 AI drafts", "200 ATS checks", "100 AI reviews"],
      cta: "Subscribe monthly",
      highlighted: false,
    },
  ];

  return (
    <section id="pricing" className="border-t border-line bg-surface/40">
      <div className="mx-auto max-w-[1240px] px-5 py-16 lg:px-8 lg:py-24">
        <div className="text-center">
          <Badge tone="lime" className="px-3 py-1 text-[9px]">
            Transparent limits
          </Badge>
          <h2 className="mt-5 font-display text-3xl tracking-[-0.02em] sm:text-4xl">
            Honest plans. <span className="italic">No surprise walls.</span>
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-muted">
            Every limit is visible before you pay. Prices exclude taxes; the checkout shows the final
            amount. Cancel Pro anytime.
          </p>
        </div>
        <div className="mx-auto mt-10 grid max-w-5xl gap-4 lg:grid-cols-3">
          {plans.map((plan) => (
            <article
              key={plan.name}
              className={`relative flex flex-col rounded-card border p-6 ${
                plan.highlighted
                  ? "border-ink bg-surface shadow-lift lg:-translate-y-3"
                  : "border-line bg-surface"
              }`}
            >
              {plan.highlighted ? (
                <Badge tone="lime" className="absolute -top-3 left-6 px-3 py-1 text-[9px]">
                  Most chosen
                </Badge>
              ) : null}
              <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted">{plan.name}</p>
              <div className="mt-5 flex items-end gap-2">
                <span className="font-display text-4xl tracking-[-0.03em]">{plan.price}</span>
                <span className="pb-1 text-xs text-muted">{plan.cadence}</span>
              </div>
              <p className="mt-2 text-sm text-muted">{plan.description}</p>
              <ul className="mt-6 flex-1 space-y-2.5">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-2 text-sm">
                    <Check size={14} className="text-forest" strokeWidth={2.5} />
                    {feature}
                  </li>
                ))}
              </ul>
              <Link to="/signup" className="mt-7">
                <Button className="w-full" variant={plan.highlighted ? "primary" : "secondary"}>
                  {plan.cta}
                </Button>
              </Link>
            </article>
          ))}
        </div>
        <p className="mt-6 text-center font-mono text-[10px] uppercase tracking-[0.12em] text-muted">
          Own AI key removes the monthly AI limits. AI reviews still need a paid plan.
        </p>
      </div>
    </section>
  );
}

const FAQS = [
  [
    "Why LaTeX instead of a drag-and-drop builder?",
    "LaTeX gives you typographic control and a PDF that parses cleanly. You can stay in the structured form and never touch a command, or open the source when you want the last five percent.",
  ],
  [
    "Do I need to know LaTeX to use Rezumiq?",
    "No. The form editor writes the LaTeX for you. Code mode is there for people who already have a .tex file or want to edit the source directly.",
  ],
  [
    "How does the ATS score actually work?",
    "We compile your PDF, read it back through a parser like the ones recruiters use, then score parsing, contact details, sections, impact, length, and job match. Every check shows its evidence.",
  ],
  [
    "Can I import my current resume?",
    "Yes. Upload a PDF, a LaTeX file, or paste text. AI extracts the structure and a rule-based pass puts back any lines the model missed.",
  ],
  [
    "What happens to my data if I cancel?",
    "Your account and resumes stay. Paid features stop at the end of the period, and you can export everything as JSON or delete the account from Settings.",
  ],
  [
    "Can I use my own AI key?",
    "Yes. Add a Groq, OpenAI, Anthropic, or OpenRouter key in Settings. It removes the monthly AI limits, but AI reviews still require a paid plan.",
  ],
];

function EditorMock() {
  return (
    <div className="relative mx-auto mt-14 max-w-5xl animate-rise">
      <div className="absolute -left-3 -top-3 z-10 hidden items-center gap-2 rounded-full border border-line bg-surface px-3 py-1.5 shadow-soft sm:flex">
        <span className="h-1.5 w-1.5 rounded-full bg-forest" />
        <span className="font-mono text-[9px] uppercase tracking-[0.12em]">ATS 92 · Optimal</span>
      </div>
      <div className="overflow-hidden rounded-card border border-line bg-surface shadow-lift">
        <div className="flex items-center justify-between border-b border-line bg-paper/80 px-3 py-2">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-line" />
            <span className="h-2 w-2 rounded-full bg-line" />
            <span className="h-2 w-2 rounded-full bg-line" />
            <span className="ml-2 font-mono text-[9px] uppercase tracking-[0.12em] text-muted">
              Editor / Stripe Staff Eng
            </span>
          </div>
          <span className="rounded-full border border-forest/20 bg-forest/5 px-2 py-0.5 font-mono text-[8px] uppercase tracking-[0.1em] text-forest">
            Saved just now
          </span>
        </div>
        <div className="grid lg:grid-cols-[1fr_1.08fr]">
          <div className="space-y-3 border-b border-line p-4 lg:border-b-0 lg:border-r">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-muted">Basics / Contact</span>
              <Badge tone="outline" className="text-[8px]">PII masked</Badge>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {["ROHAN KULKARNI", "Staff Infrastructure", "rohan@hey.com", "Bengaluru, India"].map((value, index) => (
                <div key={value} className={index > 1 ? "col-span-2" : ""}>
                  <div className="mb-1 h-1 w-8 rounded bg-line/80" />
                  <div className="truncate rounded border border-line bg-paper px-2 py-1.5 text-[10px]">{value}</div>
                </div>
              ))}
            </div>
            <div className="rounded border border-line bg-paper p-2.5">
              <div className="flex items-center justify-between">
                <span className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">Experience</span>
                <span className="text-[9px] text-muted">2 entries</span>
              </div>
              <div className="mt-2 rounded border border-line bg-surface p-2">
                <div className="flex items-center justify-between text-[10px]">
                  <span className="font-medium">Razorpay · Systems Architect</span>
                  <span className="font-mono text-[8px] text-muted">Jan 2022 - Present</span>
                </div>
                <div className="mt-2 space-y-1.5">
                  {["Architected a settlement engine at 99.995% uptime.", "Cut p99 from 180ms to 24ms with Vitess."].map(
                    (line) => (
                      <p key={line} className="rounded bg-paper px-2 py-1 text-[9px] leading-[14px] text-muted">
                        {line}
                      </p>
                    ),
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 rounded border border-lime/60 bg-lime/20 px-2.5 py-2">
              <Sparkles size={13} />
              <span className="text-[10px] font-medium">Polish summary with AI</span>
              <ArrowRight size={12} className="ml-auto" />
            </div>
          </div>
          <div className="bg-[#EDEAE2] p-4 sm:p-6">
            <div className="mx-auto aspect-[1/1.28] max-w-[340px] rounded-sm border border-line bg-white px-6 py-7 document-shadow">
              <div className="text-center">
                <p className="font-display text-[17px] tracking-[0.02em]">ROHAN KULKARNI</p>
                <p className="mt-1 font-mono text-[7px] uppercase tracking-[0.14em] text-muted">
                  Bengaluru, India · rohan@hey.com · +91 98765 43210
                </p>
              </div>
              <div className="mt-5">
                <p className="font-mono text-[7px] uppercase tracking-[0.16em]">Executive Profile</p>
                <div className="mt-1 h-px bg-ink/20" />
                <p className="mt-1.5 text-[7px] leading-3 text-muted">
                  Staff Distributed Systems Architect with 9+ years building hyper-scale transactional
                  backends and low-latency consensus clusters.
                </p>
              </div>
              <div className="mt-4">
                <p className="font-mono text-[7px] uppercase tracking-[0.16em]">Engineering Experience</p>
                <div className="mt-1 h-px bg-ink/20" />
                {[
                  ["Razorpay", "Principal Systems Architect", "Jan 2022 - Present"],
                  ["GoJek", "Senior Software Engineer", "Aug 2019 - Dec 2021"],
                ].map(([company, role, dates], index) => (
                  <div key={company} className="mt-2">
                    <div className="flex items-baseline justify-between">
                      <p className="text-[8px] font-semibold">
                        {company} <span className="font-normal text-muted">· {role}</span>
                      </p>
                      <span className="font-mono text-[6px] text-muted">{dates}</span>
                    </div>
                    <div className="mt-1 space-y-0.5">
                      {(index === 0
                        ? ["Architected settlement engine processing 14M+ daily events.", "Reduced p99 latency from 180ms to 24ms.", "Designed Raft-based state synchronization."]
                        : ["Led monolith to microservices migration for 2.2M daily rides.", "Built Kafka ingestion at 120k records/sec."]
                      ).map((bullet) => (
                        <p key={bullet} className="flex gap-1 text-[6.5px] leading-[10px] text-muted">
                          <span>•</span> {bullet}
                        </p>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4">
                <p className="font-mono text-[7px] uppercase tracking-[0.16em]">Technical Competencies</p>
                <div className="mt-1 h-px bg-ink/20" />
                <p className="mt-1.5 text-[6.5px] leading-3 text-muted">
                  <strong>Languages:</strong> Go, Rust, Java, C++, SQL, Bash, Python
                </p>
                <p className="mt-1 text-[6.5px] leading-3 text-muted">
                  <strong>Distributed Architecture:</strong> Raft Consensus, Vitess, Apache Kafka
                </p>
              </div>
            </div>
            <p className="mt-3 text-center font-mono text-[8px] uppercase tracking-[0.12em] text-muted">
              Compiled in 1.24s · Page 1 of 1
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
