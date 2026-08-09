import { describe, expect, it } from "vitest";

import { normalizeError } from "@/lib/api-errors";

function jsonResponse(status: number, body: unknown, headers: Record<string, string> = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...headers },
  });
}

describe("normalizeError", () => {
  it("normalizes this backend's custom {error, detail} shape", async () => {
    const res = jsonResponse(422, {
      error: "exercise_validation_error",
      detail: "Topic invalid.",
    });
    const result = await normalizeError(res);
    expect(result).toEqual({
      status: 422,
      code: "exercise_validation_error",
      detail: "Topic invalid.",
      requestId: undefined,
    });
  });

  it("normalizes FastAPI's default {detail: string} shape", async () => {
    const res = jsonResponse(404, { detail: "Exercise not found." });
    const result = await normalizeError(res);
    expect(result.status).toBe(404);
    expect(result.detail).toBe("Exercise not found.");
  });

  it("normalizes FastAPI's validation error array shape", async () => {
    const res = jsonResponse(422, {
      detail: [
        { loc: ["body", "topic"], msg: "field required", type: "missing" },
      ],
    });
    const result = await normalizeError(res);
    expect(result.status).toBe(422);
    expect(result.code).toBe("validation_error");
    expect(result.detail).toContain("field required");
  });

  it("falls back to a generic message for a non-JSON body", async () => {
    const res = new Response("<html>Internal Server Error</html>", {
      status: 500,
    });
    const result = await normalizeError(res);
    expect(result.status).toBe(500);
    expect(result.detail).toBeTruthy();
  });

  it("carries through the request id when present", async () => {
    const res = jsonResponse(500, { detail: "boom" });
    const result = await normalizeError(res, "req-123");
    expect(result.requestId).toBe("req-123");
  });
});
