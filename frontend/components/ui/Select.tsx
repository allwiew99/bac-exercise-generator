import type { SelectHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

type SelectProps = SelectHTMLAttributes<HTMLSelectElement>;

export function Select({ className, children, ...rest }: SelectProps) {
  return (
    <select
      className={cn(
        "rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3.5 py-2.5 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-primary)]",
        className,
      )}
      {...rest}
    >
      {children}
    </select>
  );
}
