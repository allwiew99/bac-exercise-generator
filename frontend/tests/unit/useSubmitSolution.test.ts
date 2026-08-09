import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { act, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const getIdToken = vi.fn().mockResolvedValue("id-token");
const mockAuth = { currentUser: { getIdToken } as unknown };

vi.mock("@/lib/firebase", () => ({ auth: mockAuth }));

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

beforeEach(() => {
  vi.resetModules();
  getIdToken.mockClear();
  vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "https://api.example.com");
  vi.stubEnv("NEXT_PUBLIC_USE_MOCK_API", "false");
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("useSubmitSolution", () => {
  it("never auto-retries a failed submission (only the one request lib/api.ts makes)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(500, { detail: "boom" }));
    vi.stubGlobal("fetch", fetchMock);

    const { useSubmitSolution } = await import("@/hooks/useSubmitSolution");
    const client = new QueryClient();
    const wrapper = ({ children }: { children: ReactNode }) =>
      QueryClientProvider({ client, children });

    const { result } = renderHook(() => useSubmitSolution(15), { wrapper });

    act(() => {
      result.current.mutate({ code: "int main(){}" });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    // 500 is not the 401 case, so lib/api.ts's own retry-once logic never
    // kicks in either — exactly one network call total.
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
