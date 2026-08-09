import type { Page } from "@playwright/test";

function base64url(input: object): string {
  return Buffer.from(JSON.stringify(input))
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

function fakeIdToken(uid: string, email: string): string {
  const header = base64url({ alg: "none", typ: "JWT" });
  const payload = base64url({
    sub: uid,
    user_id: uid,
    email,
    exp: Math.floor(Date.now() / 1000) + 3600,
    iat: Math.floor(Date.now() / 1000),
  });
  return `${header}.${payload}.`;
}

/**
 * Intercepts the Google Identity Toolkit / Secure Token REST endpoints the
 * Firebase Auth Web SDK calls under the hood, so the e2e smoke test can
 * exercise a real login form submission without hitting real Firebase or
 * Gemini services (per FRONTEND_HANDOFF.md §5.17: "do not hit real
 * Gemini/Firebase in CI").
 */
export async function mockFirebaseAuth(
  page: Page,
  { uid = "smoke-test-uid", email = "student@exemplu.ro" } = {},
) {
  const idToken = fakeIdToken(uid, email);

  await page.route("**/identitytoolkit.googleapis.com/**", async (route) => {
    const url = route.request().url();

    if (url.includes(":signInWithPassword") || url.includes(":signUp")) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          kind: "identitytoolkit#VerifyPasswordResponse",
          localId: uid,
          email,
          displayName: "",
          idToken,
          registered: true,
          refreshToken: "smoke-test-refresh-token",
          expiresIn: "3600",
        }),
      });
      return;
    }

    if (url.includes(":lookup")) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          kind: "identitytoolkit#GetAccountInfoResponse",
          users: [
            {
              localId: uid,
              email,
              displayName: "",
              emailVerified: true,
              providerUserInfo: [],
            },
          ],
        }),
      });
      return;
    }

    await route.continue();
  });

  await page.route("**/securetoken.googleapis.com/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: idToken,
        id_token: idToken,
        refresh_token: "smoke-test-refresh-token",
        expires_in: "3600",
        token_type: "Bearer",
        user_id: uid,
        project_id: "smoke-test-project",
      }),
    });
  });
}
