import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";
import { cn } from "@/lib/utils";

type Props = InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  hint?: string;
  error?: string;
  trailing?: ReactNode;
};

export const Input = forwardRef<HTMLInputElement, Props>(function Input(
  { className, label, hint, error, trailing, id, ...props },
  ref,
) {
  const inputId = id ?? props.name;
  return (
    <label className="block">
      {label ? (
        <span className="mb-1.5 block font-mono text-[10px] uppercase tracking-[0.16em] text-muted">
          {label}
        </span>
      ) : null}
      <span className="relative block">
        <input
          ref={ref}
          id={inputId}
          className={cn(
            "focus-ring h-11 w-full rounded-field border border-line bg-surface px-3.5 text-sm text-ink placeholder:text-muted/60",
            error && "border-danger/60 focus-visible:ring-danger",
            trailing && "pr-11",
            className,
          )}
          {...props}
        />
        {trailing ? <span className="absolute inset-y-0 right-3 flex items-center">{trailing}</span> : null}
      </span>
      {error ? <span className="mt-1 block text-xs text-danger">{error}</span> : null}
      {!error && hint ? <span className="mt-1 block text-xs text-muted">{hint}</span> : null}
    </label>
  );
});
