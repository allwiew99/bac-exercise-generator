"use client";

import { signOut } from "firebase/auth";
import { useRouter } from "next/navigation";
import { use, useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import {
  CPP_STARTER_TEMPLATE,
  CppEditor,
} from "@/components/exercises/CppEditor";
import { ExerciseDetails } from "@/components/exercises/ExerciseDetails";
import { SubmissionResult } from "@/components/exercises/SubmissionResult";
import { PageContainer } from "@/components/layout/PageContainer";
import { Button } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/ErrorState";
import { ExerciseDetailSkeleton } from "@/components/ui/Skeleton";
import { useExercise } from "@/hooks/useExercise";
import { useSubmitSolution } from "@/hooks/useSubmitSolution";
import { auth } from "@/lib/firebase";
import { SubmitSolutionRequestSchema } from "@/schemas/submission";


function SolveExercise({ id }: { id: number }) {
  const router = useRouter();

  const {
    data: exercise,
    isPending,
    error,
    refetch,
  } = useExercise(id);

  const [code, setCode] = useState(
    CPP_STARTER_TEMPLATE
  );

  const [codeError, setCodeError] = useState("");

  const submission = useSubmitSolution(id);


  useEffect(() => {
    if (
      submission.error &&
      submission.error.status === 401
    ) {
      signOut(auth).finally(() => {
        router.push(
          `/login?next=/exercises/${id}`
        );
      });
    }
  }, [
    submission.error,
    router,
    id,
  ]);


  if (isPending) {
    return (
      <PageContainer>
        <ExerciseDetailSkeleton />
      </PageContainer>
    );
  }


  if (error) {
    return (
      <ErrorState
        error={error}
        onRetry={() => refetch()}
        backHref="/exercises"
      />
    );
  }


  if (!exercise) {
    return null;
  }


  const handleSubmit = () => {
    if (submission.isPending) {
      return;
    }

    const result =
      SubmitSolutionRequestSchema.safeParse({
        code,
      });

    if (!result.success) {
      setCodeError(
        result.error.issues[0]?.message
          ?? "Cod invalid."
      );

      return;
    }

    setCodeError("");

    submission.mutate(result.data);
  };


  const submissionErrorMessage =
    submission.error &&
    submission.error.status !== 401
      ? submission.error.status === 429
        ? (
            "Ai atins limita de trimiteri. "
            + "Te rugăm să încerci din nou mai târziu."
          )
        : (
            "Verificarea soluției nu a putut fi procesată. "
            + "Încearcă din nou."
          )
      : undefined;


  return (
    <>
      <ExerciseDetails
          exercise={exercise}
          variant="detail"
        />

      <section className="mx-auto max-w-[840px] px-6 pb-16">
        <h2 className="mb-3 font-display text-lg font-semibold">
          Rezolvarea ta
        </h2>

        <CppEditor
          value={code}
          onChange={(next) => {
            setCode(next);
            setCodeError("");
          }}
          disabled={submission.isPending}
        />

        {codeError ? (
          <div className="mt-2 text-[13px] text-[var(--color-danger)]">
            {codeError}
          </div>
        ) : null}

        {submissionErrorMessage ? (
          <div className="mt-3 rounded-lg bg-[var(--color-danger-bg)] px-3.5 py-3 text-[13px] text-[var(--color-danger)]">
            {submissionErrorMessage}
          </div>
        ) : null}

        <Button
          onClick={handleSubmit}
          disabled={submission.isPending}
          className="mt-4"
        >
          {submission.isPending
            ? "Se verifică..."
            : "Verifică soluția"}
        </Button>

        {submission.data || exercise.has_submitted ? (
          <SubmissionResult
            submission={submission.data}
            exerciseId={id}
            persistedProgress={
              exercise.has_submitted
                ? {
                    latestScore:
                      exercise.latest_score,
                    submissionCount:
                      exercise.submission_count,
                    completed:
                      exercise.completed,
                  }
                : undefined
            }
          />
        ) : null}
      </section>
    </>
  );
}


export default function ExerciseDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  const numericId = Number(id);

  if (!Number.isFinite(numericId)) {
    return (
      <ErrorState
        error={{
          status: 404,
          code: "not_found",
          detail:
            "Exercițiul căutat nu există sau a fost șters.",
        }}
        backHref="/exercises"
      />
    );
  }

  return (
    <ProtectedRoute>
      <SolveExercise id={numericId} />
    </ProtectedRoute>
  );
}