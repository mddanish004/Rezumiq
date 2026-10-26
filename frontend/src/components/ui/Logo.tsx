import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";

export function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <Link to="/" className={cn("group inline-flex items-center gap-2.5", className)} aria-label="Rezumiq home">
      <span className="grid h-8 w-8 place-items-center rounded-full border border-ink bg-ink font-display text-[15px] italic text-paper transition-colors group-hover:bg-forest group-hover:border-forest">
        R
      </span>
      {!compact ? (
        <span className="flex flex-col leading-none">
          <span className="font-display text-[19px] tracking-[-0.02em]">Rezumiq</span>
          <span className="mt-1 font-mono text-[8px] uppercase tracking-[0.2em] text-muted">
            Editorial ATS
          </span>
        </span>
      ) : null}
    </Link>
  );
}
