import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Check, ArrowLeft } from "lucide-react";
import { Logo } from "@/components/ui/Logo";

export function AuthLayout({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="grid min-h-screen bg-paper lg:grid-cols-[0.9fr_1.1fr]">
      <aside className="relative hidden overflow-hidden border-r border-line bg-ink px-10 py-10 text-paper lg:flex lg:flex-col">
        <div className="pointer-events-none absolute inset-0 opacity-[0.12] paper-grid" />
        <div className="relative">
          <Logo className="[&_span]:text-paper" />
        </div>
        <div className="relative mt-auto max-w-md pb-10">
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-paper/45">A quieter resume studio</p>
          <h2 className="mt-4 font-display text-4xl leading-[1.04] tracking-[-0.02em]">
            Write it once.
            <br />
            <span className="italic text-lime">Prove it parses.</span>
          </h2>
          <p className="mt-5 text-sm leading-7 text-paper/60">
            Real LaTeX PDFs, version history, a rule-based ATS report, and job tailoring you approve line
            by line.
          </p>
          <ul className="mt-8 space-y-3">
            {[
              "Two editors, one resume",
              "Import PDF, LaTeX, or text",
              "No invented facts in AI drafts",
            ].map((item) => (
              <li key={item} className="flex items-center gap-2.5 text-sm text-paper/80">
                <span className="grid h-5 w-5 place-items-center rounded-full border border-paper/20">
                  <Check size={11} className="text-lime" strokeWidth={3} />
                </span>
                {item}
              </li>
            ))}
          </ul>
        </div>
        <div className="relative flex items-center justify-between border-t border-paper/15 pt-5 font-mono text-[9px] uppercase tracking-[0.14em] text-paper/40">
          <span>Rezumiq / 2026</span>
          <span>LaTeX · ATS · Share</span>
        </div>
      </aside>

      <main className="flex flex-col px-5 py-6 sm:px-10 lg:px-16">
        <div className="flex items-center justify-between lg:justify-end">
          <div className="lg:hidden">
            <Logo />
          </div>
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-xs text-muted transition-colors hover:text-ink"
          >
            <ArrowLeft size={13} /> Back to site
          </Link>
        </div>
        <div className="mx-auto flex w-full max-w-[420px] flex-1 flex-col justify-center py-12">
          <h1 className="font-display text-3xl tracking-[-0.02em]">{title}</h1>
          <p className="mt-2 text-sm leading-6 text-muted">{subtitle}</p>
          <div className="mt-8">{children}</div>
          {footer ? <div className="mt-6 text-sm text-muted">{footer}</div> : null}
        </div>
      </main>
    </div>
  );
}
