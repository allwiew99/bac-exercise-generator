import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SubmissionResult } from "@/components/exercises/SubmissionResult";
import type { Submission } from "@/schemas/submission";

const useOfficialSolutionMock = vi.fn();

vi.mock("@/hooks/useOfficialSolution", () => ({
  useOfficialSolution: (...args: unknown[]) => useOfficialSolutionMock(...args),
}));

function baseSubmission(overrides: Partial<Submission> = {}): Submission {
  return {
    id: 1,
    exercise_id: 15,
    score: 100,
    passed_tests: 4,
    total_tests: 4,
    status: "passed",
    feedback: null,
    created_at: "2026-08-08T10:00:00",
    ...overrides,
  };
}

beforeEach(() => {
  useOfficialSolutionMock.mockReturnValue({
    data: undefined,
    isFetching: false,
    error: undefined,
    refetch: vi.fn(),
  });
});

describe("SubmissionResult", () => {
  it("renders the passed state without humiliating or alarming copy", () => {
    render(<SubmissionResult submission={baseSubmission()} exerciseId={15} />);
    expect(screen.getByText("Scor: 100/100")).toBeInTheDocument();
    expect(screen.getByText("4 din 4 teste trecute")).toBeInTheDocument();
    expect(screen.getByText("Toate testele au trecut.")).toBeInTheDocument();
  });

  it("renders the partial state with passed/total and feedback", () => {
    render(
      <SubmissionResult
        submission={baseSubmission({
          status: "partial",
          score: 75,
          passed_tests: 3,
          feedback: "Verifică cazurile limită.",
        })}
        exerciseId={15}
      />,
    );
    expect(screen.getByText("Scor: 75/100")).toBeInTheDocument();
    expect(screen.getByText("3 din 4 teste trecute")).toBeInTheDocument();
    expect(screen.getByText("Verifică cazurile limită.")).toBeInTheDocument();
  });

  it("renders compilation_error feedback as sanitized compiler output, not a stack trace", () => {
    render(
      <SubmissionResult
        submission={baseSubmission({
          status: "compilation_error",
          score: 0,
          passed_tests: 0,
          feedback: "error: expected ';' before '}' token",
        })}
        exerciseId={15}
      />,
    );
    expect(screen.getByText("Compilarea a eșuat.")).toBeInTheDocument();
    expect(
      screen.getByText("error: expected ';' before '}' token"),
    ).toBeInTheDocument();
  });

  it("renders runtime_error with friendly copy", () => {
    render(
      <SubmissionResult
        submission={baseSubmission({ status: "runtime_error", score: 0 })}
        exerciseId={15}
      />,
    );
    expect(
      screen.getByText("Execuția a eșuat în timpul rulării testelor."),
    ).toBeInTheDocument();
  });

  it("falls back to a neutral treatment for an unrecognized status", () => {
    render(
      <SubmissionResult
        submission={baseSubmission({ status: "queued_for_review" })}
        exerciseId={15}
      />,
    );
    expect(screen.getByText("Status: queued_for_review")).toBeInTheDocument();
  });

  it("does not fetch the official solution until the reveal button is clicked", async () => {
    const refetch = vi.fn();
    useOfficialSolutionMock.mockReturnValue({
      data: undefined,
      isFetching: false,
      error: undefined,
      refetch,
    });
    render(<SubmissionResult submission={baseSubmission()} exerciseId={15} />);

    expect(refetch).not.toHaveBeenCalled();
    await userEvent.click(
      screen.getByRole("button", { name: /Vezi soluția oficială/ }),
    );
    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it("renders the official solution and explanation toggle once revealed", async () => {
    useOfficialSolutionMock.mockReturnValue({
      data: { solution: "int main() { return 0; }", explanation: "De ce." },
      isFetching: false,
      error: undefined,
      refetch: vi.fn(),
    });
    render(<SubmissionResult submission={baseSubmission()} exerciseId={15} />);

    expect(screen.getByText("Soluție C++")).toBeInTheDocument();
    expect(screen.queryByText("De ce.")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /Explicație/ }));
    expect(screen.getByText("De ce.")).toBeInTheDocument();
  });
});
