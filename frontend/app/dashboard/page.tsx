"use client";

import { signOut } from "firebase/auth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { ExerciseDetails } from "@/components/exercises/ExerciseDetails";
import { ExerciseForm } from "@/components/exercises/ExerciseForm";
import { GenerationLoadingState } from "@/components/exercises/GenerationLoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { useGenerateExercise } from "@/hooks/useGenerateExercise";
import { auth } from "@/lib/firebase";
import { hasId } from "@/schemas/exercise";

function DashboardContent() {
  const router = useRouter();
  const mutation = useGenerateExercise();
  const { data, error, isPending, reset } = mutation;

  useEffect(() => {
    if (data && hasId(data)) {
      router.push(`/exercises/${data.id}`);
    }
  }, [data, router]);

  useEffect(() => {
    if (error && error.status === 401) {
      signOut(auth).finally(() => {
        router.push("/login?next=/dashboard");
      });
    }
  }, [error, router]);

  if (isPending) {
    return <GenerationLoadingState />;
  }

  if (data && !hasId(data)) {
    return (
      <ExerciseDetails
        exercise={data}
        variant="result"
        onGenerateAnother={reset}
      />
    );
  }

  if (error && error.status === 429) {
    return <ErrorState error={error} />;
  }

  if (error && error.status >= 500) {
    const retry = mutation.variables
      ? () => mutation.mutate(mutation.variables!)
      : undefined;
    return <ErrorState error={error} onRetry={retry} />;
  }

  const formError =
    error && (error.status === 400 || error.status === 422)
      ? "Cererea nu a putut fi procesată. Verifică subiectul introdus."
      : undefined;

  return (
    <section className="mx-auto max-w-[640px] px-6 py-16">
      <h1 className="mb-2 font-display text-[28px] font-semibold">
        Generează un exercițiu
      </h1>
      <p className="mb-8 text-[15px] text-[var(--color-text-secondary)]">
        Alege un subiect și un nivel, apoi lasă AI-ul să genereze și să
        valideze exercițiul.
      </p>
      <ExerciseForm
        busy={isPending}
        formError={formError}
        onSubmit={(request) => mutation.mutate(request)}
      />
    </section>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}
