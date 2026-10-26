import type { ReactNode } from "react";

export function EmptyState({
  title,
  description,
  action,
  icon,
}: {
  title: string;
  description: string;
  action?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-start gap-3 rounded-card border border-dashed border-line bg-paper/60 p-6">
      {icon ? <div className="text-muted">{icon}</div> : null}
      <div>
        <p className="font-display text-lg text-ink">{title}</p>
        <p className="mt-1 max-w-md text-sm leading-6 text-muted">{description}</p>
      </div>
      {action}
    </div>
  );
}
