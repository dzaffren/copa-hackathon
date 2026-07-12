/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/ — Vitest `test` block is augmented via the
// triple-slash reference above so a single config covers dev, build, and tests.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/setupTests.ts",
    css: false,
    // Vitest owns the unit/component tests under `src/` only. Playwright E2E
    // specs live in `tests/e2e/*.spec.ts` and use `@playwright/test`, which
    // throws under Vitest — scope the runner to `src/` so the two never collide.
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
  },
});
