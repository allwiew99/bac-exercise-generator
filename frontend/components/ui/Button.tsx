import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "ghost";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  children: ReactNode;
};

const VARIANT_CLASSES: Record<Variant, string> = {
  primary:
    "bg-[var(--color-primary)] text-white border border-transparent hover:opacity-90",
  secondary:
    "bg-transparent text-[var(--color-text)] border border-[var(--color-border)] hover:bg-[var(--color-surface)]",
  ghost:
    "bg-transparent text-[var(--color-text-secondary)] border border-transparent hover:text-[var(--color-text)]",
};

export function Button({
  variant = "primary",
  className,
  disabled,
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      disabled={disabled}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg px-5 py-3 text-sm font-bold transition-opacity",
        disabled && "cursor-not-allowed opacity-60",
        VARIANT_CLASSES[variant],
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}
