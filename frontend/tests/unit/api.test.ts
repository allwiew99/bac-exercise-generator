import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const getIdToken = vi.fn().mockResolvedValue("id-token");
const mockAuth = {
  currentUser: { getIdToken } as unknown,
};

vi.mock("@/lib/firebase", () => ({
  auth: mockAuth,
}));

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

beforeEach(() => {
  vi.resetModules();
  getIdToken.mockClear();
  mockAuth.currentUser = { getIdToken };
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("lib/api.ts request()", () => {
  it("retries exactly once with a forced token refresh on a 401, then succeeds", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "https://api.example.com");
    vi.stubEnv("NEXT_PUBLIC_USE_MOCK_API", "false");

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: "expired" }))
      .mockResolvedValueOnce(
        jsonResponse(200, [
          {
            id: 1,
            topic: "vectori",
            difficulty: "easy",
            statement: "s",
            solution: "sol",
            explanation: "e",
            created_at: "2026-08-01T00:00:00",
            test_cases: [],
          },
        ]),
      );
    vi.stubGlobal("fetch", fetchMock);

    const { listExercises } = await import("@/lib/api");
    const result = await listExercises();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(getIdToken).toHaveBeenNthCalledWith(1, false);
    expect(getIdToken).toHaveBeenNthCalledWith(2, true);
    expect(result).toHaveLength(1);
  });

  it("does not retry a second time if the retried request is still 401", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "https://api.example.com");
    vi.stubEnv("NEXT_PUBLIC_USE_MOCK_API", "false");

    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(401, { detail: "still expired" }));
    vi.stubGlobal("fetch", fetchMock);

    const { listExercises } = await import("@/lib/api");

    await expect(listExercises()).rejects.toMatchObject({ status: 401 });
    expect(fetchMock).toHaveBeenCalledTimes(2); // original + one retry, no more
  });

  it("normalizes a fetch/network failure instead of throwing raw", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "https://api.example.com");
    vi.stubEnv("NEXT_PUBLIC_USE_MOCK_API", "false");

    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    );

    const { listExercises } = await import("@/lib/api");

    await expect(listExercises()).rejects.toMatchObject({
      status: 0,
      code: "network_error",
    });
  });
});

describe("lib/api.ts submitSolution() / getOfficialSolution()", () => {
  it("POSTs to /exercises/{id}/submissions with the code body, no user_id", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "https://api.example.com");
    vi.stubEnv("NEXT_PUBLIC_USE_MOCK_API", "false");

    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        id: 1,
        exercise_id: 15,
        score: 100,
        passed_tests: 1,
        total_tests: 1,
        status: "passed",
        created_at: "2026-08-08T10:00:00",
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const { submitSolution } = await import("@/lib/api");
    const result = await submitSolution(15, { code: "int main(){}" });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("https://api.example.com/exercises/15/submissions");
    expect(init.method).toBe("POST");
    const sentBody = JSON.parse(init.body as string);
    expect(sentBody).toEqual({ code: "int main(){}" });
    expect(sentBody).not.toHaveProperty("user_id");
    expect(result.status).toBe("passed");
  });

  it("calls GET /exercises/{id}/solution for the official solution", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "https://api.example.com");
    vi.stubEnv("NEXT_PUBLIC_USE_MOCK_API", "false");

    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        jsonResponse(200, { solution: "int main(){}", explanation: "..." }),
      );
    vi.stubGlobal("fetch", fetchMock);

    const { getOfficialSolution } = await import("@/lib/api");
    await getOfficialSolution(15);

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("https://api.example.com/exercises/15/solution");
    expect(init.method).toBe("GET");
  });

  it("in mock mode, only exposes the official solution after a mocked submission", async () => {
    vi.stubEnv("NEXT_PUBLIC_USE_MOCK_API", "true");
    vi.stubEnv("NODE_ENV", "development");

    const { submitSolution, getOfficialSolution, listExercises } =
      await import("@/lib/api");

    const [{ id }] = await listExercises();

    await expect(getOfficialSolution(id)).rejects.toMatchObject({
      status: 403,
    });

    await submitSolution(id, { code: "int main() { return 0; }" });
    const solution = await getOfficialSolution(id);
    expect(solution.solution).toContain("include");
  });
});

describe("MOCK_MODE_ENABLED gating", () => {
  it("is true only when both the flag is set and NODE_ENV is not production", async () => {
    vi.stubEnv("NEXT_PUBLIC_USE_MOCK_API", "true");
    vi.stubEnv("NODE_ENV", "development");
    const { MOCK_MODE_ENABLED } = await import("@/lib/api");
    expect(MOCK_MODE_ENABLED).toBe(true);
  });

  it("is false in a production build even if the flag is left true", async () => {
    vi.stubEnv("NEXT_PUBLIC_USE_MOCK_API", "true");
    vi.stubEnv("NODE_ENV", "production");
    const { MOCK_MODE_ENABLED } = await import("@/lib/api");
    expect(MOCK_MODE_ENABLED).toBe(false);
  });

  it("is false when the flag is unset", async () => {
    vi.stubEnv("NEXT_PUBLIC_USE_MOCK_API", "false");
    vi.stubEnv("NODE_ENV", "development");
    const { MOCK_MODE_ENABLED } = await import("@/lib/api");
    expect(MOCK_MODE_ENABLED).toBe(false);
  });
});
