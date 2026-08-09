import { defineConfig, devices } from "@playwright/test";

// Smoke-only, per the handoff: exercises one flow with Firebase/backend
// mocked (NEXT_PUBLIC_USE_MOCK_API=true). Never hits real Gemini/Firebase.
export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "npm run dev -- --port 3100",
    url: "http://127.0.0.1:3100",
    timeout: 60_000,
    reuseExistingServer: !process.env.CI,
    env: {
      NEXT_PUBLIC_USE_MOCK_API: "true",
      NEXT_PUBLIC_API_BASE_URL: "http://127.0.0.1:9",
      NEXT_PUBLIC_FIREBASE_API_KEY: "test-api-key",
      NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN: "test.firebaseapp.com",
      NEXT_PUBLIC_FIREBASE_PROJECT_ID: "test-project",
      NEXT_PUBLIC_FIREBASE_APP_ID: "test-app-id",
      NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID: "1234567890",
    },
  },
});
