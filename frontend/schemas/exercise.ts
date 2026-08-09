import { z } from "zod";

export const DifficultySchema = z.enum([
  "easy",
  "medium",
  "hard",
]);

export const TestCaseSchema = z.object({
  input: z.string(),
  expected_output: z.string(),
});

export const ExerciseSafeSchema = z.object({
  id: z.number(),
  topic: z.string(),
  difficulty: DifficultySchema,
  statement: z.string(),
  created_at: z.string(),

  sample_test_cases: z.array(TestCaseSchema).optional(),

  has_submitted: z.boolean().optional(),

  latest_score: z
    .number()
    .nullable()
    .optional(),

  submission_count: z.number().optional(),

  completed: z.boolean().optional(),
});

export const ExerciseListSchema = z.array(
  ExerciseSafeSchema
);

export const GeneratedExerciseNoIdSchema = z.object({
  topic: z.string(),
  difficulty: DifficultySchema,
  statement: z.string(),
  sample_test_cases: z.array(TestCaseSchema).optional(),
});

export const GeneratedExerciseSchema = z.union([
  ExerciseSafeSchema,
  GeneratedExerciseNoIdSchema,
]);

export const GenerateExerciseRequestSchema = z.object({
  topic: z
    .string()
    .trim()
    .min(1, "Te rugăm să introduci un subiect.")
    .max(80, "Subiectul este prea lung."),
  difficulty: DifficultySchema,
});

export type Difficulty = z.infer<
  typeof DifficultySchema
>;

export type TestCase = z.infer<
  typeof TestCaseSchema
>;

export type ExerciseSafe = z.infer<
  typeof ExerciseSafeSchema
>;

export type GeneratedExerciseNoId = z.infer<
  typeof GeneratedExerciseNoIdSchema
>;

export type GeneratedExercise = z.infer<
  typeof GeneratedExerciseSchema
>;

export type GenerateExerciseRequest = z.infer<
  typeof GenerateExerciseRequestSchema
>;

export function hasId(
  exercise: GeneratedExercise,
): exercise is ExerciseSafe {
  return "id" in exercise;
}