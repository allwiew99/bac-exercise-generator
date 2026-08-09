import { useQuery } from "@tanstack/react-query";

import { listExercises } from "@/lib/api";
import type { ApiError } from "@/lib/api-errors";
import type { ExerciseSafe } from "@/schemas/exercise";

export function useExercises() {
  return useQuery<ExerciseSafe[], ApiError>({
    queryKey: ["exercises"],
    queryFn: listExercises,
  });
}
