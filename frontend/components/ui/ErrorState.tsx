"use client";

import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/Button";
import type { ApiError } from "@/lib/api-errors";

type ErrorCode = "401" | "403" | "404" | "429" | "500";

type ErrorMeta = {
  code: ErrorCode;
  title: string;
  detail: string;
  actionLabel: string;
};

const ERROR_META: Record<ErrorCode, ErrorMeta> = {
  "401": {
    code: "401",
    title: "Sesiune expirată",
    detail: "Sesiunea ta a expirat. Te rugăm să te autentifici din nou.",
    actionLabel: "Autentificare",
  },
  "403": {
    code: "403",
    title: "Acces interzis",
    detail: "Nu ai acces la acest exercițiu.",
    actionLabel: "Înapoi la exercițiile mele",
  },
  "404": {
    code: "404",
    title: "Exercițiu negăsit",
    detail: "Exercițiul căutat nu există sau a fost șters.",
    actionLabel: "Înapoi la exercițiile mele",
  },
  "429": {
    code: "429",
    title: "Limită atinsă",
    detail:
      "Ai atins limita de generări. Te rugăm să încerci din nou mai târziu.",
    actionLabel: "Înapoi la panou",
  },
  "500": {
    code: "500",
    title: "Eroare de server",
    detail: "A apărut o problemă neașteptată. Te rugăm să încerci din nou.",
    actionLabel: "Încearcă din nou",
  },
};

function statusToCode(status: number): ErrorCode {
  if (status === 401) return "401";
  if (status === 403) return "403";
  if (status === 404) return "404";
  if (status === 429) return "429";
  return "500";
}

export function errorStateCode(error: ApiError): ErrorCode {
  return statusToCode(error.status);
}

export function ErrorState({
  error,
  onRetry,
  backHref = "/exercises",
}: {
  error: ApiError;
  onRetry?: () => void;
  backHref?: string;
}) {
  const router = useRouter();
  const code = statusToCode(error.status);
  const meta = ERROR_META[code];

  const handleAction = () => {
    if (code === "401") {
      router.push("/login");
      return;
    }
    if (code === "403" || code === "404") {
      router.push(backHref);
      return;
    }
    if (code === "429") {
      router.push("/dashboard");
      return;
    }
    onRetry?.();
  };

  return (
    <section className="mx-auto max-w-md px-6 py-28 text-center">
      <div className="mx-auto mb-5 flex h-13 w-13 items-center justify-center rounded-2xl bg-[var(--color-danger-bg)] font-display text-xl font-bold text-[var(--color-danger)]">
        {meta.code}
      </div>
      <h2 className="mb-2.5 font-display text-xl font-semibold">
        {meta.title}
      </h2>
      <p className="mb-6 text-sm leading-relaxed text-[var(--color-text-secondary)]">
        {meta.detail}
      </p>
      {error.requestId ? (
        <p className="mb-6 text-xs text-[var(--color-text-secondary)]">
          ID cerere: {error.requestId}
        </p>
      ) : null}
      <Button onClick={handleAction}>{meta.actionLabel}</Button>
    </section>
  );
}
