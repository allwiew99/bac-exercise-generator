import { z } from "zod";


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


export const OfficialSolutionSchema = z.object({
  solution: z.string(),
  explanation: z.string(),
});

export type Submission = z.infer<typeof SubmissionSchema>;
export type SubmitSolutionRequest = z.infer<typeof SubmitSolutionRequestSchema>;
export type OfficialSolution = z.infer<typeof OfficialSolutionSchema>;
