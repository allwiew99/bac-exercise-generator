import { useMutation, useQueryClient } from "@tanstack/react-query";

import { generateExercise } from "@/lib/api";
import type { ApiError } from "@/lib/api-errors";
import type { GenerateExerciseRequest, GeneratedExercise } from "@/schemas/exercise";

export function useGenerateExercise() {
  const queryClient = useQueryClient();

  return useMutation<GeneratedExercise, ApiError, GenerateExerciseRequest>({
    mutationFn: (body: GenerateExerciseRequest) => generateExercise(body),
    // Generation has real AI/compute cost and could create duplicate
    // exercises on retry — never retried automatically (see lib/query-client.ts).
    retry: false,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exercises"] });
    },
  });
}
