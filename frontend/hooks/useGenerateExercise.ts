import { useMutation, useQueryClient } from "@tanstack/react-query";

import { generateExercise } from "@/lib/api";
import type { ApiError } from "@/lib/api-errors";
import type { GenerateExerciseRequest, GeneratedExercise } from "@/schemas/exercise";

export function useGenerateExercise() {
  const queryClient = useQueryClient();

  return useMutation<GeneratedExercise, ApiError, GenerateExerciseRequest>({
    mutationFn: (body: GenerateExerciseRequest) => generateExercise(body),
    retry: false,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exercises"] });
    },
  });
}
