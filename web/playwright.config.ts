// Playwright E2E configuration for the Rulebook Radar workspace (#7).
//
// This is the harness the drafter epic's UI stories (#26 / #8 / #9 / #10) reuse.
// Specs live in `tests/e2e/*.spec.ts` (owned by the component tasks) and import
// `installEngineStub` from `tests/e2e/fixtures/engineStub.ts` to serve the real
// corpus deterministically and offline — no Python engine runs during E2E.
//
// The `webServer` block boots the Vite dev server on its default port (5173) and
// injects `VITE_ENGINE_BASE_URL` so the app targets the intercepted stub origin
// (see `engineStub.ts`). Browsers are installed separately at the E2E gate
// (`npx playwright install chromium`); running the specs is out of scope here.

import { defineConfig, devices } from "@playwright/test";

import { ENGINE_STUB_BASE_URL } from "./tests/e2e/fixtures/engineStub";

/** Vite dev server origin — Vite's default host/port. Also the app's baseURL. */
const BASE_URL = "http://localhost:5173";

export default defineConfig({
  testDir: "./tests/e2e",
  // Fail fast if a test accidentally left a `.only` in the suite.
  forbidOnly: true,
  fullyParallel: true,
  retries: 0,
  reporter: "list",
  // Generous but bounded: the corpus is tiny and every engine call is stubbed.
  timeout: 30_000,
  expect: { timeout: 5_000 },

  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
  },

  // A single Chromium project (bundled Chromium, not the branded channel).
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  // Boot the Vite dev server for the suite; reuse one already running locally.
  webServer: {
    command: "npm run dev",
    url: BASE_URL,
    reuseExistingServer: true,
    timeout: 120_000,
    // Point the app at the stub origin; `engineStub` intercepts every call to it.
    env: { VITE_ENGINE_BASE_URL: ENGINE_STUB_BASE_URL },
  },
});
