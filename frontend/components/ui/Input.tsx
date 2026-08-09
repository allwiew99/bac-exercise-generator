import type { InputHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

type InputProps = InputHTMLAttributes<HTMLInputElement>;

export function Input({ className, ...rest }: InputProps) {
  return (
    <input
      className={cn(
        "w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3.5 py-2.5 text-sm text-[var(--color-text)] outline-none placeholder:text-[var(--color-text-secondary)] focus:border-[var(--color-primary)]",
        className,
      )}
      {...rest}
    />
  );
}
