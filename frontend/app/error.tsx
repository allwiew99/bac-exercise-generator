"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/Button";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") {
      console.error(error);
    }
  }, [error]);

  return (
    <section className="mx-auto max-w-md px-6 py-28 text-center">
      <div className="mx-auto mb-5 flex h-13 w-13 items-center justify-center rounded-2xl bg-[var(--color-danger-bg)] font-display text-xl font-bold text-[var(--color-danger)]">
        !
      </div>
      <h2 className="mb-2.5 font-display text-xl font-semibold">
        A apărut o eroare neașteptată
      </h2>
      <p className="mb-6 text-sm leading-relaxed text-[var(--color-text-secondary)]">
        Ceva nu a funcționat corect. Te rugăm să încerci din nou.
      </p>
      <Button onClick={reset}>Încearcă din nou</Button>
    </section>
  );
}
