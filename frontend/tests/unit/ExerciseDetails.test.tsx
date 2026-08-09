import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ExerciseDetails } from "@/components/exercises/ExerciseDetails";
import type { ExerciseSafe, GeneratedExerciseNoId } from "@/schemas/exercise";

const persistedExercise: ExerciseSafe = {
  id: 15,
  topic: "vectori",
  difficulty: "medium",
  statement: "Enunțul exercițiului.",
  created_at: "2026-08-01T09:12:00",
  sample_test_cases: [{ input: "1 2", expected_output: "3" }],
};

const noIdExercise: GeneratedExerciseNoId = {
  topic: "vectori",
  difficulty: "medium",
  statement: "Enunțul exercițiului.",
};

describe("ExerciseDetails", () => {
  it("never renders the official solution or explanation before submission", () => {
    render(<ExerciseDetails exercise={persistedExercise} variant="detail" />);
    expect(screen.queryByText("Soluție C++")).not.toBeInTheDocument();
    expect(screen.queryByText("Explicație")).not.toBeInTheDocument();
  });

  it("renders sample test cases as examples, not as the full grading criteria", () => {
    render(<ExerciseDetails exercise={persistedExercise} variant="detail" />);
    expect(screen.getByText("Exemple de teste")).toBeInTheDocument();
    expect(screen.getByText("1 2")).toBeInTheDocument();
    expect(screen.queryByText("Cazuri de test")).not.toBeInTheDocument();
  });

  it("renders no test-case panel when the backend sends no sample tests", () => {
    render(<ExerciseDetails exercise={noIdExercise} variant="result" />);
    expect(screen.queryByText("Exemple de teste")).not.toBeInTheDocument();
  });

  it("shows the back link on the detail variant and the transitional note + CTAs on the result variant", () => {
    const { rerender } = render(
      <ExerciseDetails exercise={persistedExercise} variant="detail" />,
    );
    expect(
      screen.getByText("← Înapoi la exercițiile mele"),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Generează altul" }),
    ).not.toBeInTheDocument();

    rerender(<ExerciseDetails exercise={noIdExercise} variant="result" />);
    expect(
      screen.queryByText("← Înapoi la exercițiile mele"),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Generează altul" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/identificator persistent/)).toBeInTheDocument();
  });
});
