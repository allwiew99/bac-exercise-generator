import { describe, expect, it } from "vitest";

import {
  ExerciseListSchema,
  ExerciseSafeSchema,
  GeneratedExerciseSchema,
  GenerateExerciseRequestSchema,
  hasId,
} from "@/schemas/exercise";

const legacyFullExercisePayload = {
  id: 42,
  topic: "vectori",
  difficulty: "medium",
  statement: "Enunț.",
  created_at: "2026-08-01T09:12:00",
  solution: "int main() { return 0; }",
  explanation: "Explicație.",
  test_cases: [{ input: "1", expected_output: "1" }],
};

const legacyNoIdGeneratePayload = {
  topic: "vectori",
  difficulty: "medium",
  statement: "Enunț.",
  solution: "int main() { return 0; }",
  explanation: "Explicație.",
  test_cases: [{ input: "1", expected_output: "1" }],
};

describe("ExerciseSafeSchema", () => {
  it("strips solution/explanation/test_cases from today's full backend payload", () => {
    const result = ExerciseSafeSchema.parse(legacyFullExercisePayload);
    expect(result).not.toHaveProperty("solution");
    expect(result).not.toHaveProperty("explanation");
    expect(result).not.toHaveProperty("test_cases");
    expect(result.id).toBe(42);
    expect(result.topic).toBe("vectori");
  });

  it("keeps sample_test_cases and progress fields when the backend sends them", () => {
    const result = ExerciseSafeSchema.parse({
      ...legacyFullExercisePayload,
      sample_test_cases: [{ input: "1", expected_output: "1" }],
      has_submitted: true,
      latest_score: 80,
      submission_count: 2,
      completed: false,
    });
    expect(result.sample_test_cases).toHaveLength(1);
    expect(result.has_submitted).toBe(true);
    expect(result.latest_score).toBe(80);
    expect(result.submission_count).toBe(2);
    expect(result.completed).toBe(false);
  });
});

describe("ExerciseListSchema", () => {
  it("strips hidden fields from every item in a list response", () => {
    const result = ExerciseListSchema.parse([legacyFullExercisePayload]);
    expect(result[0]).not.toHaveProperty("solution");
    expect(result[0]).not.toHaveProperty("test_cases");
  });
});

describe("GeneratedExerciseSchema", () => {
  it("strips solution/explanation from today's no-id generate response", () => {
    const result = GeneratedExerciseSchema.parse(legacyNoIdGeneratePayload);
    expect(hasId(result)).toBe(false);
    expect(result).not.toHaveProperty("solution");
    expect(result).not.toHaveProperty("explanation");
    expect(result).not.toHaveProperty("test_cases");
  });

  it("strips solution/explanation from the target persisted (with-id) shape", () => {
    const result = GeneratedExerciseSchema.parse(legacyFullExercisePayload);
    expect(hasId(result)).toBe(true);
    expect(result).not.toHaveProperty("solution");
    if (hasId(result)) {
      expect(result.id).toBe(42);
    }
  });

  it("rejects an invalid difficulty", () => {
    const invalid = { ...legacyNoIdGeneratePayload, difficulty: "extreme" };
    expect(() => GeneratedExerciseSchema.parse(invalid)).toThrow();
  });
});

describe("GenerateExerciseRequestSchema", () => {
  it("trims and accepts a valid topic", () => {
    const result = GenerateExerciseRequestSchema.parse({
      topic: "  vectori  ",
      difficulty: "easy",
    });
    expect(result.topic).toBe("vectori");
  });

  it("rejects an empty topic", () => {
    const result = GenerateExerciseRequestSchema.safeParse({
      topic: "   ",
      difficulty: "easy",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a topic longer than 80 characters", () => {
    const result = GenerateExerciseRequestSchema.safeParse({
      topic: "a".repeat(81),
      difficulty: "easy",
    });
    expect(result.success).toBe(false);
  });
});
