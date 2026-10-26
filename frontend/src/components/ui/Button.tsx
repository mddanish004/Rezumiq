import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "dark" | "danger";
type Size = "sm" | "md" | "lg" | "icon";

const variants: Record<Variant, string> = {
  primary:
    "bg-lime text-ink border border-lime hover:bg-lime-dark hover:border-lime-dark shadow-soft",
  secondary:
    "bg-surface text-ink border border-line hover:border-ink/30 hover:bg-paper shadow-soft",
  ghost: "bg-transparent text-ink border border-transparent hover:bg-ink/5",
  dark: "bg-ink text-white border border-ink hover:bg-ink/90",
  danger: "bg-danger text-white border border-danger hover:bg-danger/90",
};

const sizes: Record<Size, string> = {
  sm: "h-9 px-3 text-[13px] gap-1.5",
  md: "h-10 px-4 text-sm gap-2",
  lg: "h-12 px-5 text-[15px] gap-2",
  icon: "h-10 w-10",
};

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
  children?: ReactNode;
};

export function Button({ className, variant = "primary", size = "md", type = "button", ...props }: Props) {
  return (
    <button
      type={type}
      className={cn(
        "focus-ring inline-flex items-center justify-center rounded-field font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    />
  );
}
