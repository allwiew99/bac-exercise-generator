import { useQuery } from "@tanstack/react-query";

import { getExerciseById } from "@/lib/api";
import type { ApiError } from "@/lib/api-errors";
import type { ExerciseSafe } from "@/schemas/exercise";

export function useExercise(id: number) {
  return useQuery<ExerciseSafe, ApiError>({
    queryKey: ["exercises", id],
    queryFn: () => getExerciseById(id),
    enabled: Number.isFinite(id),
  });
}
