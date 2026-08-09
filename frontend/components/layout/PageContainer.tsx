import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

export function PageContainer({
  children,
  className,
  maxWidth = "840px",
}: {
  children: ReactNode;
  className?: string;
  maxWidth?: string;
}) {
  return (
    <section
      className={cn("mx-auto px-6", className)}
      style={{ maxWidth }}
    >
      {children}
    </section>
  );
}
