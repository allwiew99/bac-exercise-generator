"use client";

import { useState } from "react";

import { CodeBlock } from "@/components/exercises/CodeBlock";
import { useOfficialSolution } from "@/hooks/useOfficialSolution";
import {
  STATUS_TONE_CLASSES,
  submissionStatusMeta,
} from "@/lib/submission-status";
import type { Submission } from "@/schemas/submission";


const COMPILER_OUTPUT_STATUSES = new Set([
  "compilation_error",
  "runtime_error",
]);


type PersistedProgress = {
  latestScore: number | null | undefined;
  submissionCount: number | undefined;
  completed: boolean | undefined;
};


export function SubmissionResult({
  submission,
  exerciseId,
  persistedProgress,
}: {
  submission?: Submission;
  exerciseId: number;
  persistedProgress?: PersistedProgress;
}) {
  const [showExplanation, setShowExplanation] = useState(false);
  const solutionQuery = useOfficialSolution(exerciseId);

  const hasLiveSubmission = submission !== undefined;

  const score = hasLiveSubmission
    ? submission.score
    : persistedProgress?.latestScore ?? null;

  const completed = hasLiveSubmission
    ? submission.status === "passed"
    : persistedProgress?.completed ?? false;

  const submissionCount =
    persistedProgress?.submissionCount ?? 0;

  const meta = hasLiveSubmission
    ? submissionStatusMeta(submission.status)
    : completed
      ? submissionStatusMeta("passed")
      : submissionStatusMeta("partial");

  const message = hasLiveSubmission
    ? submission.feedback ?? meta.defaultMessage
    : completed
      ? "Exercițiul a fost rezolvat complet."
      : "Ai trimis deja cel puțin o soluție pentru acest exercițiu.";

  const isCompilerOutput =
    hasLiveSubmission &&
    COMPILER_OUTPUT_STATUSES.has(submission.status);

  const handleReveal = () => {
    if (!solutionQuery.isFetching) {
      solutionQuery.refetch();
    }
  };

  return (
    <section className="mt-6 space-y-4">
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
        <span
          className={`mb-3 inline-block rounded-full px-3 py-1 text-xs font-bold ${
            STATUS_TONE_CLASSES[meta.tone]
          }`}
        >
          Status: {meta.label}
        </span>

        {score !== null ? (
          <div className="text-2xl font-bold">
            Scor: {score}/100
          </div>
        ) : null}

        {hasLiveSubmission ? (
          <div className="mt-1 text-sm text-[var(--color-text-secondary)]">
            {submission.passed_tests} din{" "}
            {submission.total_tests} teste trecute
          </div>
        ) : submissionCount > 0 ? (
          <div className="mt-1 text-sm text-[var(--color-text-secondary)]">
            Încercări trimise: {submissionCount}
          </div>
        ) : null}

        <div className="mt-4 font-semibold">
          {meta.heading}
        </div>

        {message ? (
          isCompilerOutput ? (
            <pre className="mt-2 overflow-x-auto whitespace-pre-wrap rounded-lg bg-[var(--color-code-bg)] p-3 text-sm">
              {message}
            </pre>
          ) : (
            <div className="mt-2 text-sm">
              {message}
            </div>
          )
        ) : null}
      </div>

      <div className="overflow-hidden rounded-xl border border-[var(--color-border)]">
        {solutionQuery.data ? (
          <>
            <div className="bg-[var(--color-surface)] px-5 py-4 text-[15px] font-semibold">
              Soluție C++
            </div>

            <CodeBlock code={solutionQuery.data.solution} />

            <button
              type="button"
              onClick={() =>
                setShowExplanation((value) => !value)
              }
              className="flex w-full items-center justify-between border-t border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-4 text-left"
            >
              <span className="text-[15px] font-semibold">
                Explicație
              </span>

              <span className="text-[13px] text-[var(--color-text-secondary)]">
                {showExplanation ? "Ascunde" : "Arată"}
              </span>
            </button>

            {showExplanation ? (
              <div className="border-t border-[var(--color-border)] px-5 py-5 text-[14.5px] leading-relaxed whitespace-pre-wrap">
                {solutionQuery.data.explanation}
              </div>
            ) : null}
          </>
        ) : (
          <button
            type="button"
            onClick={handleReveal}
            disabled={solutionQuery.isFetching}
            className="flex w-full items-center justify-between bg-[var(--color-surface)] px-5 py-4 text-left disabled:cursor-not-allowed disabled:opacity-60"
          >
            <span className="text-[15px] font-semibold">
              Vezi soluția oficială
            </span>

            <span className="text-[13px] text-[var(--color-text-secondary)]">
              {solutionQuery.isFetching
                ? "Se încarcă..."
                : "Arată"}
            </span>
          </button>
        )}

        {solutionQuery.error ? (
          <div className="border-t border-[var(--color-border)] bg-[var(--color-danger-bg)] px-5 py-3 text-[13px] text-[var(--color-danger)]">
            {solutionQuery.error.detail}
          </div>
        ) : null}
      </div>
    </section>
  );
}