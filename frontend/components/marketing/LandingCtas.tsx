"use client";

import Link from "next/link";

import { useAuth } from "@/hooks/useAuth";

export function LandingCtas() {
  const { user, loading } = useAuth();

  return (
    <div className="flex flex-wrap justify-center gap-3.5">
      <Link
        href="/dashboard"
        className="rounded-lg bg-[var(--color-primary)] px-7 py-3.5 text-[15px] font-bold text-white no-underline hover:no-underline"
      >
        Generează un exercițiu
      </Link>
      {!loading && !user ? (
        <Link
          href="/login"
          className="rounded-lg border border-[var(--color-border)] px-7 py-3.5 text-[15px] font-bold text-[var(--color-text)] no-underline hover:no-underline"
        >
          Autentificare
        </Link>
      ) : null}
    </div>
  );
}
