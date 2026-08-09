import { useQuery } from "@tanstack/react-query";

import { getOfficialSolution } from "@/lib/api";
import type { ApiError } from "@/lib/api-errors";
import type { OfficialSolution } from "@/schemas/submission";

/**
 * `enabled: false` always — this must never fire on mount or as a side
 * effect of exercise/submission data changing. The caller triggers it via
 * `refetch()` in response to an explicit "Vezi soluția oficială" click,
 * and only offers that action once it knows a submission exists for this
 * exercise (see components/exercises/SubmissionResult.tsx). Backend
 * authorization is still the real gate — this is UX sequencing only.
 */
export function useOfficialSolution(exerciseId: number) {
  return useQuery<OfficialSolution, ApiError>({
    queryKey: ["exercises", exerciseId, "solution"],
    queryFn: () => getOfficialSolution(exerciseId),
    enabled: false,
    retry: false,
  });
}
