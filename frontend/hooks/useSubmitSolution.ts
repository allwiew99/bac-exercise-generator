import { useMutation, useQueryClient } from "@tanstack/react-query";

import { submitSolution } from "@/lib/api";
import type { ApiError } from "@/lib/api-errors";
import type { SubmitSolutionRequest, Submission } from "@/schemas/submission";

export function useSubmitSolution(exerciseId: number) {
  const queryClient = useQueryClient();

  return useMutation<Submission, ApiError, SubmitSolutionRequest>({
    mutationFn: (body) => submitSolution(exerciseId, body),
    // Compiling + running hidden tests has real cost and a submission is a
    // graded record — never retried automatically, same rationale as
    // useGenerateExercise.
    retry: false,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exercises", exerciseId] });
      queryClient.invalidateQueries({ queryKey: ["exercises"] });
    },
  });
}
