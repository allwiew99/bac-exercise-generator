import { z } from "zod";

/**
 * Known statuses the UI has a specific visual treatment for. Kept as a
 * plain string in the schema below (not a closed enum) so an unrecognized
 * future status from the backend doesn't fail parsing — components fall
 * back to a neutral, generic treatment for anything not in this list. See
 * lib/submission-status.ts.
 */
export const KNOWN_SUBMISSION_STATUSES = [
  "passed",
  "partial",
  "failed",
  "compilation_error",
  "runtime_error",
] as const;

export type KnownSubmissionStatus = (typeof KNOWN_SUBMISSION_STATUSES)[number];

export const SubmissionSchema = z.object({
  id: z.number(),
  exercise_id: z.number(),
  score: z.number(),
  passed_tests: z.number(),
  total_tests: z.number(),
  status: z.string(),
  feedback: z.string().nullable().optional(),
  created_at: z.string(),
});

export const SubmitSolutionRequestSchema = z.object({
  code: z.string().trim().min(1, "Scrie o soluție înainte de a trimite."),
});

/**
 * Future GET /exercises/{exercise_id}/solution response — backend should
 * only return this once its authorization rules allow it (today: after at
 * least one submission for that exercise).
 */
export const OfficialSolutionSchema = z.object({
  solution: z.string(),
  explanation: z.string(),
});

export type Submission = z.infer<typeof SubmissionSchema>;
export type SubmitSolutionRequest = z.infer<typeof SubmitSolutionRequestSchema>;
export type OfficialSolution = z.infer<typeof OfficialSolutionSchema>;
