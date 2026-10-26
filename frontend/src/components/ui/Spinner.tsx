import { cn } from "@/lib/utils";

export function Spinner({ className, label }: { className?: string; label?: string }) {
  return (
    <div className={cn("flex items-center gap-3 text-sm text-muted", className)}>
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-line border-t-ink" />
      {label ? <span>{label}</span> : null}
    </div>
  );
}
