import Link from "next/link";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { TestCasesList } from "@/components/exercises/TestCasesList";
import { DIFFICULTY_LABEL } from "@/lib/difficulty";
import { formatDateRo } from "@/lib/format-date";
import type { GeneratedExercise } from "@/schemas/exercise";
import { hasId } from "@/schemas/exercise";

type Props = {
  exercise: GeneratedExercise;
  /** "result": just-generated, no persisted id yet (transitional — see
   *  README "Future Backend Dependencies"), shows the post-generate CTAs
   *  and a note that solving requires the backend's persisted-id contract.
   *  "detail": persisted exercise viewed from `/exercises/[id]`, shows a
   *  back link. Neither variant renders the official solution or
   *  explanation — those only appear after a submission, in
   *  SubmissionResult. */
  variant: "result" | "detail";
  onGenerateAnother?: () => void;
};

export function ExerciseDetails({ exercise, variant, onGenerateAnother }: Props) {
  const createdLabel = hasId(exercise)
    ? `Generat pe ${formatDateRo(exercise.created_at)}`
    : "";
  const sampleTestCases =
    "sample_test_cases" in exercise ? exercise.sample_test_cases : undefined;

  return (
    <section className="mx-auto max-w-[840px] px-6 pt-12 pb-25">
      {variant === "detail" ? (
        <Link
          href="/exercises"
          className="mb-4 inline-block text-[13px] font-semibold text-[var(--color-text-secondary)]"
        >
          ← Înapoi la exercițiile mele
        </Link>
      ) : null}

      <div className="mb-3 flex flex-wrap items-center gap-2.5">
        <Badge>{exercise.topic}</Badge>
        <Badge>{DIFFICULTY_LABEL[exercise.difficulty]}</Badge>
        {createdLabel ? (
          <span className="text-[13px] text-[var(--color-text-secondary)]">
            {createdLabel}
          </span>
        ) : null}
      </div>

      <h1 className="mb-7 font-display text-2xl leading-snug font-semibold whitespace-pre-wrap">
        {exercise.statement}
      </h1>

      {sampleTestCases && sampleTestCases.length > 0 ? (
        <div className="mb-7">
          <TestCasesList
            testCases={sampleTestCases}
            title="Exemple de teste"
          />
        </div>
      ) : null}

      {variant === "result" ? (
        <>
          <p className="mb-6 rounded-lg bg-[var(--color-accent-bg)] px-4 py-3 text-sm text-[var(--color-text-secondary)]">
            Rezolvarea acestui exercițiu necesită ca exercițiul să fie
            salvat cu un identificator persistent — funcționalitate
            disponibilă imediat ce backend-ul returnează exercițiul salvat.
            Deocamdată poți citi enunțul mai jos.
          </p>
          <div className="flex gap-3">
            <Button variant="secondary" onClick={onGenerateAnother}>
              Generează altul
            </Button>
            <Link
              href="/exercises"
              className="inline-flex items-center justify-center rounded-lg border border-transparent bg-[var(--color-primary)] px-5 py-3 text-sm font-bold text-white no-underline hover:no-underline"
            >
              Vezi exercițiile mele
            </Link>
          </div>
        </>
      ) : null}
    </section>
  );
}
