import { useQuery } from "@tanstack/react-query";

import { getOfficialSolution } from "@/lib/api";
import type { ApiError } from "@/lib/api-errors";
import type { OfficialSolution } from "@/schemas/submission";


export function useOfficialSolution(exerciseId: number) {
  return useQuery<OfficialSolution, ApiError>({
    queryKey: ["exercises", exerciseId, "solution"],
    queryFn: () => getOfficialSolution(exerciseId),
    enabled: false,
    retry: false,
  });
}
