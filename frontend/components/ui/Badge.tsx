import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

export function Badge({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-block rounded-full bg-[var(--color-accent-bg)] px-3 py-1 text-xs font-bold text-[var(--color-primary)]",
        className,
      )}
    >
      {children}
    </span>
  );
}
