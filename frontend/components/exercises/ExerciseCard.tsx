import Link from "next/link";

import { Badge } from "@/components/ui/Badge";
import { DIFFICULTY_LABEL } from "@/lib/difficulty";
import { formatDateRo } from "@/lib/format-date";
import type { ExerciseSafe } from "@/schemas/exercise";

export function ExerciseCard({ exercise }: { exercise: ExerciseSafe }) {
  
  const hasProgressInfo =
    exercise.latest_score !== undefined ||
    exercise.submission_count !== undefined ||
    exercise.completed !== undefined;

  return (
    <Link
      href={`/exercises/${exercise.id}`}
      className="flex items-center justify-between gap-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-4.5 no-underline hover:no-underline"
    >
      <div>
        <div className="mb-1.5 text-[15px] font-semibold text-[var(--color-text)]">
          {exercise.topic}
        </div>
        <div className="text-[13px] text-[var(--color-text-secondary)]">
          {formatDateRo(exercise.created_at)}
        </div>
        {hasProgressInfo ? (
          <div className="mt-1.5 text-[12.5px] text-[var(--color-text-secondary)]">
            {exercise.completed ? "Rezolvat" : null}
            {exercise.completed && exercise.latest_score !== undefined
              ? " · "
              : null}
            {exercise.latest_score !== undefined
              ? `Ultimul scor: ${exercise.latest_score}/100`
              : null}
            {exercise.submission_count !== undefined
              ? ` · ${exercise.submission_count} încercări`
              : null}
          </div>
        ) : null}
      </div>
      <div className="flex items-center gap-3.5">
        <Badge>{DIFFICULTY_LABEL[exercise.difficulty]}</Badge>
        <span className="text-[var(--color-text-secondary)]">→</span>
      </div>
    </Link>
  );
}
