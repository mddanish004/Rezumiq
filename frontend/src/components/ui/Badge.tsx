import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Tone = "neutral" | "lime" | "dark" | "success" | "warning" | "danger" | "outline";

const tones: Record<Tone, string> = {
  neutral: "bg-soft text-ink border-transparent",
  lime: "bg-lime text-ink border-lime",
  dark: "bg-ink text-white border-ink",
  success: "bg-success/10 text-success border-success/20",
  warning: "bg-warning/10 text-warning border-warning/20",
  danger: "bg-danger/10 text-danger border-danger/20",
  outline: "bg-transparent text-muted border-line",
};

export function Badge({
  className,
  tone = "neutral",
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.12em]",
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}
