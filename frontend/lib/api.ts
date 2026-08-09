import type { ZodType } from "zod";

import {
  type ApiError,
  networkError,
  normalizeError,
} from "@/lib/api-errors";
import { auth } from "@/lib/firebase";
import { mockApi } from "@/lib/mock-api";
import {
  ExerciseListSchema,
  ExerciseSafeSchema,
  type ExerciseSafe,
  type GenerateExerciseRequest,
  type GeneratedExercise,
  GeneratedExerciseSchema,
} from "@/schemas/exercise";
import {
  OfficialSolutionSchema,
  SubmissionSchema,
  type OfficialSolution,
  type Submission,
  type SubmitSolutionRequest,
} from "@/schemas/submission";


// Mock mode is available only during development.
// It cannot activate accidentally in production.
export const MOCK_MODE_ENABLED =
  process.env.NEXT_PUBLIC_USE_MOCK_API === "true" &&
  process.env.NODE_ENV !== "production";


type RequestOptions = RequestInit & {
  schema: ZodType;

  /**
   * Attach the Firebase ID token.
   * Defaults to true.
   */
  auth?: boolean;
};


async function request(
  path: string,
  opts: RequestOptions,
): Promise<unknown> {
  const baseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL;

  if (!baseUrl) {
    throw {
      status: 0,
      code: "config_error",
      detail: "URL-ul serverului nu este configurat.",
    } satisfies ApiError;
  }

  const {
    schema,
    auth: useAuth = true,
    ...init
  } = opts;

  const run = async (
    forceRefresh: boolean,
  ): Promise<Response> => {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(
        (init.headers as Record<string, string>)
        ?? {}
      ),
    };

    if (useAuth) {
      const user = auth.currentUser;

      if (user) {
        const idToken = await user.getIdToken(
          forceRefresh
        );

        headers.Authorization =
          `Bearer ${idToken}`;
      }
    }

    return fetch(
      `${baseUrl}${path}`,
      {
        ...init,
        headers,
      }
    );
  };


  let res: Response;

  try {
    res = await run(false);
  } catch {
    throw networkError();
  }


  // Firebase tokens can expire.
  // Retry exactly once with a refreshed token.
  if (
    res.status === 401 &&
    auth.currentUser
  ) {
    try {
      res = await run(true);
    } catch {
      throw networkError();
    }
  }


  const requestId =
    res.headers.get("x-request-id")
    ?? undefined;


  if (!res.ok) {
    throw await normalizeError(
      res,
      requestId,
    );
  }


  const json = await res.json();

  return schema.parse(json);
}


export async function generateExercise(
  body: GenerateExerciseRequest,
): Promise<GeneratedExercise> {
  if (MOCK_MODE_ENABLED) {
    return mockApi.generateExercise(body);
  }

  return request(
    "/exercises/generate",
    {
      method: "POST",
      body: JSON.stringify(body),
      schema: GeneratedExerciseSchema,
    },
  ) as Promise<GeneratedExercise>;
}


export async function listExercises(): Promise<
  ExerciseSafe[]
> {
  if (MOCK_MODE_ENABLED) {
    return mockApi.listExercises();
  }

  return request(
    "/exercises/",
    {
      method: "GET",
      schema: ExerciseListSchema,
    },
  ) as Promise<ExerciseSafe[]>;
}


export async function getExerciseById(
  id: number,
): Promise<ExerciseSafe> {
  if (MOCK_MODE_ENABLED) {
    return mockApi.getExerciseById(id);
  }

  return request(
    `/exercises/${id}`,
    {
      method: "GET",
      schema: ExerciseSafeSchema,
    },
  ) as Promise<ExerciseSafe>;
}


/**
 * Submit the student's C++ solution.
 *
 * Backend:
 * POST /exercises/{exercise_id}/submissions
 */
export async function submitSolution(
  exerciseId: number,
  body: SubmitSolutionRequest,
): Promise<Submission> {
  if (MOCK_MODE_ENABLED) {
    return mockApi.submitSolution(
      exerciseId,
      body,
    );
  }

  return request(
    `/exercises/${exerciseId}/submissions`,
    {
      method: "POST",
      body: JSON.stringify(body),
      schema: SubmissionSchema,
    },
  ) as Promise<Submission>;
}


/**
 * Retrieve the official solution.
 *
 * Backend allows this only after the student
 * has made at least one submission.
 *
 * GET /exercises/{exercise_id}/solution
 */
export async function getOfficialSolution(
  exerciseId: number,
): Promise<OfficialSolution> {
  if (MOCK_MODE_ENABLED) {
    return mockApi.getOfficialSolution(
      exerciseId
    );
  }

  return request(
    `/exercises/${exerciseId}/solution`,
    {
      method: "GET",
      schema: OfficialSolutionSchema,
    },
  ) as Promise<OfficialSolution>;
}


export type { ApiError };