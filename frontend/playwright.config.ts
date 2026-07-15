import { defineConfig, devices } from "@playwright/test";

// Playwright config for the Workstream Graph E2E. Not part of the default
// `npm run test` (Vitest) run. See e2e/README.md for the one-time setup.
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 5_000 },
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  // Starts the Vite dev server for the run. The FastAPI engine must be started
  // separately and VITE_API_BASE pointed at it (see e2e/README.md).
  webServer: {
    command: "npm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
