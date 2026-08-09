export type ApiError = {
  status: number;
  code: string;
  detail: string;
  requestId?: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

/**
 * Normalizes every backend/network failure shape into a single ApiError so
 * every consumer (TanStack Query `error`, form handlers) branches only on
 * `status`/`code`. Handles: `{error, detail}` (this backend's custom
 * exception handlers), FastAPI's default `{detail}` (string or a pydantic
 * validation array), and non-JSON/network failures. Never surfaces raw
 * response bodies or stack traces to the UI.
 */
export async function normalizeError(
  res: Response,
  requestId?: string,
): Promise<ApiError> {
  let body: unknown;
  try {
    body = await res.json();
  } catch {
    body = undefined;
  }

  let code = "http_error";
  let detail = "A apărut o eroare neașteptată. Te rugăm să încerci din nou.";

  if (isRecord(body)) {
    if (typeof body.error === "string") {
      code = body.error;
    }
    if (typeof body.detail === "string") {
      detail = body.detail;
    } else if (Array.isArray(body.detail)) {
      // FastAPI validation error array: [{ loc, msg, type }, ...]
      const messages = body.detail
        .map((item) =>
          isRecord(item) && typeof item.msg === "string" ? item.msg : null,
        )
        .filter((msg): msg is string => msg !== null);
      if (messages.length > 0) {
        detail = messages.join(" ");
      }
      if (code === "http_error") {
        code = "validation_error";
      }
    }
  }

  return { status: res.status, code, detail, requestId };
}

export function networkError(): ApiError {
  return {
    status: 0,
    code: "network_error",
    detail:
      "Nu am putut contacta serverul. Verifică conexiunea la internet și încearcă din nou.",
  };
}
