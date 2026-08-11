"use client";

import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { DifficultySelector } from "@/components/exercises/DifficultySelector";
import { TopicSuggestions } from "@/components/exercises/TopicSuggestions";
import {
  GenerateExerciseRequestSchema,
  type Difficulty,
  type GenerateExerciseRequest,
} from "@/schemas/exercise";

export function ExerciseForm({
  busy,
  onSubmit,
  formError,
}: {
  busy: boolean;
  onSubmit: (request: GenerateExerciseRequest) => void;
  
  formError?: string;
}) {
  const [topic, setTopic] = useState("");
  const [difficulty, setDifficulty] = useState<Difficulty>("medium");
  const [topicError, setTopicError] = useState("");

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (busy) return;

    const result = GenerateExerciseRequestSchema.safeParse({
      topic,
      difficulty,
    });
    if (!result.success) {
      setTopicError(result.error.issues[0]?.message ?? "Subiect invalid.");
      return;
    }
    setTopicError("");
    onSubmit(result.data);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-[14px] border border-[var(--color-border)] bg-[var(--color-surface)] p-7"
    >
      {formError ? (
        <div className="mb-4.5 rounded-lg bg-[var(--color-danger-bg)] px-3.5 py-3 text-[13px] text-[var(--color-danger)]">
          {formError}
        </div>
      ) : null}

      <label className="mb-2 block text-[13px] font-semibold">Subiect</label>
      <Input
        type="text"
        value={topic}
        onChange={(e) => {
          setTopic(e.target.value);
          setTopicError("");
        }}
        placeholder="ex: vectori, recursivitate, matrice..."
        maxLength={80}
      />
      {topicError ? (
        <div className="mt-1.5 text-[13px] text-[var(--color-danger)]">
          {topicError}
        </div>
      ) : null}

      <TopicSuggestions
        onPick={(picked) => {
          setTopic(picked);
          setTopicError("");
        }}
      />

      <label className="mt-6 mb-2 block text-[13px] font-semibold">
        Dificultate
      </label>
      <DifficultySelector value={difficulty} onChange={setDifficulty} />

      <Button
        type="submit"
        disabled={busy}
        className="mt-7 w-full py-3.5 text-[15px]"
      >
        Generează exercițiul
      </Button>
    </form>
  );
}
