---
name: vitest-playwright-spec-collision
description: In web/, scope Vitest test.include to src/** so it never collects Playwright *.spec.ts
type: convention
captured: 2026-07-12
source: /build session (#7 single-draft Rulebook Workspace, web/ frontend)
---

In `web/`, the Vitest config (`web/vite.config.ts`) must scope
`test.include` to `["src/**/*.{test,spec}.{ts,tsx}"]` so the unit runner
never collects the Playwright E2E specs under `web/tests/e2e/*.spec.ts`.

**Why:** Vitest and Playwright both claim the `*.spec.ts` extension, and
both live under the same `web/` tree. With Vitest's default glob, `npm test`
sweeps up the Playwright specs and crashes with "Playwright Test did not
expect test.describe() to be called here", because those specs import
`@playwright/test`, which throws when run under Vitest. Narrowing the include
to `src/` keeps the two runners from colliding.

**How to apply:** For any `web/` story that adds Playwright E2E specs under
`tests/e2e/` (e.g. #8 ripple, #9 copilot, #26 reference radar, #10
supervisor), keep unit/component tests under `src/` and leave
`test.include` scoped to `src/**`. If `npm test` suddenly fails with a
Playwright `test.describe()` error, an unscoped or widened Vitest include is
the first thing to check.
