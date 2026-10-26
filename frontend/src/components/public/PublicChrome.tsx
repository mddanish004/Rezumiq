import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import { Logo } from "@/components/ui/Logo";

export function PublicChrome({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <header className="border-b border-line bg-paper/95 backdrop-blur">
        <div className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between px-4 sm:px-6">
          <Link to="/" className="focus-ring rounded" aria-label="Rezumiq home">
            <Logo />
          </Link>
          <Link
            to="/signup"
            className="focus-ring inline-flex items-center gap-1 rounded-field border border-line bg-surface px-2.5 py-1.5 text-[12px] hover:border-ink/30"
          >
            Build yours <ArrowUpRight size={12} />
          </Link>
        </div>
      </header>
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:px-6 sm:py-12">{children}</main>
      <footer className="border-t border-line bg-paper">
        <div className="mx-auto flex w-full max-w-5xl flex-wrap items-center justify-between gap-2 px-4 py-5 text-[11px] text-muted sm:px-6">
          <span>Shared with Rezumiq.</span>
          <span className="font-mono uppercase tracking-[0.12em]">Editorial ATS resumes</span>
        </div>
      </footer>
    </div>
  );
}
