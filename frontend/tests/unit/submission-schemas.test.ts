import { describe, expect, it } from "vitest";

import {
  OfficialSolutionSchema,
  SubmissionSchema,
  SubmitSolutionRequestSchema,
} from "@/schemas/submission";

describe("SubmissionSchema", () => {
  it("parses the target conceptual shape", () => {
    const result = SubmissionSchema.parse({
      id: 1,
      exercise_id: 15,
      score: 75,
      passed_tests: 3,
      total_tests: 4,
      status: "partial",
      feedback: "Mai încearcă.",
      created_at: "2026-08-08T10:00:00",
    });
    expect(result.status).toBe("partial");
    expect(result.score).toBe(75);
  });

  it("does not reject a status value the frontend doesn't specifically know about yet", () => {
    // Deliberately not over-constrained per the product spec — a backend
    // adding a new status shouldn't require a synchronized frontend release
    // just to avoid a parse failure.
    const result = SubmissionSchema.safeParse({
      id: 1,
      exercise_id: 15,
      score: 0,
      passed_tests: 0,
      total_tests: 4,
      status: "queued_for_manual_review",
      created_at: "2026-08-08T10:00:00",
    });
    expect(result.success).toBe(true);
  });

  it("allows feedback to be absent or null", () => {
    const noFeedback = SubmissionSchema.safeParse({
      id: 1,
      exercise_id: 15,
      score: 100,
      passed_tests: 4,
      total_tests: 4,
      status: "passed",
      created_at: "2026-08-08T10:00:00",
    });
    const nullFeedback = SubmissionSchema.safeParse({
      id: 1,
      exercise_id: 15,
      score: 100,
      passed_tests: 4,
      total_tests: 4,
      status: "passed",
      feedback: null,
      created_at: "2026-08-08T10:00:00",
    });
    expect(noFeedback.success).toBe(true);
    expect(nullFeedback.success).toBe(true);
  });
});

describe("SubmitSolutionRequestSchema", () => {
  it("rejects empty code", () => {
    const result = SubmitSolutionRequestSchema.safeParse({ code: "   " });
    expect(result.success).toBe(false);
  });

  it("accepts non-empty code and does not require user_id", () => {
    const result = SubmitSolutionRequestSchema.parse({
      code: "int main() { return 0; }",
    });
    expect(result).not.toHaveProperty("user_id");
    expect(result.code).toContain("main");
  });
});

describe("OfficialSolutionSchema", () => {
  it("parses solution + explanation", () => {
    const result = OfficialSolutionSchema.parse({
      solution: "int main() { return 0; }",
      explanation: "Pentru că da.",
    });
    expect(result.solution).toContain("main");
    expect(result.explanation).toBe("Pentru că da.");
  });
});
