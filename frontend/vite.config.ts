/// <reference types="vitest/config" />
import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Dev-only: proxy API calls to the engine (uvicorn on :8000) so the browser
  // makes same-origin /api requests — the engine has no CORS middleware.
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: true,
    // Vitest owns the component/unit tests under src/. Playwright owns e2e/;
    // exclude it so the browser specs are never collected by vitest.
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
  },
});
