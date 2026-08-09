"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { ExerciseCard } from "@/components/exercises/ExerciseCard";
import {
  ExerciseFilters,
  type DifficultyFilter,
} from "@/components/exercises/ExerciseFilters";
import { ErrorState } from "@/components/ui/ErrorState";
import { ExerciseListSkeleton } from "@/components/ui/Skeleton";
import { useExercises } from "@/hooks/useExercises";

function HistoryContent() {
  const { data, isPending, error, refetch } = useExercises();
  const [filterTopic, setFilterTopic] = useState("");
  const [filterDifficulty, setFilterDifficulty] =
    useState<DifficultyFilter>("all");

  const filtered = useMemo(() => {
    if (!data) return [];
    const topicQuery = filterTopic.trim().toLowerCase();
    return data.filter((exercise) => {
      const matchesDifficulty =
        filterDifficulty === "all" || exercise.difficulty === filterDifficulty;
      const matchesTopic =
        !topicQuery || exercise.topic.toLowerCase().includes(topicQuery);
      return matchesDifficulty && matchesTopic;
    });
  }, [data, filterTopic, filterDifficulty]);

  return (
    <section className="mx-auto max-w-[840px] px-6 pt-14 pb-25">
      <h1 className="mb-6 font-display text-[26px] font-semibold">
        Exercițiile mele
      </h1>

      {isPending ? (
        <ExerciseListSkeleton />
      ) : error ? (
        <ErrorState error={error} onRetry={() => refetch()} />
      ) : (
        <>
          <ExerciseFilters
            topic={filterTopic}
            onTopicChange={setFilterTopic}
            difficulty={filterDifficulty}
            onDifficultyChange={setFilterDifficulty}
          />
          {filtered.length === 0 ? (
            <div className="px-5 py-15 text-center text-[var(--color-text-secondary)]">
              <p className="mb-4">Niciun exercițiu găsit.</p>
              <Link
                href="/dashboard"
                className="inline-flex items-center justify-center rounded-lg bg-[var(--color-primary)] px-5 py-2.75 text-sm font-semibold text-white no-underline hover:no-underline"
              >
                Generează primul tău exercițiu
              </Link>
            </div>
          ) : (
            <div className="flex flex-col gap-2.5">
              {filtered.map((exercise) => (
                <ExerciseCard key={exercise.id} exercise={exercise} />
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}

export default function ExercisesPage() {
  return (
    <ProtectedRoute>
      <HistoryContent />
    </ProtectedRoute>
  );
}
