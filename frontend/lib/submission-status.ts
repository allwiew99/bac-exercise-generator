import type { KnownSubmissionStatus } from "@/schemas/submission";

export type StatusTone = "success" | "partial" | "danger" | "neutral";

type StatusMeta = {
  label: string;
  tone: StatusTone;
  heading: string;
  
  defaultMessage: string;
};

const KNOWN_STATUS_META: Record<KnownSubmissionStatus, StatusMeta> = {
  passed: {
    label: "Corect",
    tone: "success",
    heading: "Toate testele au trecut.",
    defaultMessage: "Felicitări, soluția ta este corectă!",
  },
  partial: {
    label: "Parțial corect",
    tone: "partial",
    heading: "Soluția ta trece o parte dintre teste.",
    defaultMessage: "Mai încearcă — ești pe drumul cel bun.",
  },
  failed: {
    label: "Incorect",
    tone: "danger",
    heading: "Soluția nu a trecut testele.",
    defaultMessage: "Recitește enunțul și încearcă din nou.",
  },
  compilation_error: {
    label: "Eroare de compilare",
    tone: "danger",
    heading: "Compilarea a eșuat.",
    defaultMessage: "Verifică sintaxa codului C++ și încearcă din nou.",
  },
  runtime_error: {
    label: "Eroare de execuție",
    tone: "danger",
    heading: "Execuția a eșuat în timpul rulării testelor.",
    defaultMessage: "Verifică logica programului și încearcă din nou.",
  },
};

function isKnownStatus(status: string): status is KnownSubmissionStatus {
  return status in KNOWN_STATUS_META;
}


export function submissionStatusMeta(status: string): StatusMeta {
  if (isKnownStatus(status)) {
    return KNOWN_STATUS_META[status];
  }
  return {
    label: status,
    tone: "neutral",
    heading: "Rezultat disponibil.",
    defaultMessage: "",
  };
}

export const STATUS_TONE_CLASSES: Record<StatusTone, string> = {
  success: "bg-[var(--color-accent-bg)] text-[var(--color-success)]",
  partial: "bg-[var(--color-accent-bg)] text-[var(--color-warning)]",
  danger: "bg-[var(--color-danger-bg)] text-[var(--color-danger)]",
  neutral: "bg-[var(--color-accent-bg)] text-[var(--color-text-secondary)]",
};
