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


export async function mockFirebaseAuth(
  page: Page,
  { uid = "smoke-test-uid", email = "student@exemplu.ro" } = {},
) {
  const idToken = fakeIdToken(uid, email);

  await page.route("**/identitytoolkit.googleapis.comsecuretoken.googleapis.com/**", async (route) => {
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
