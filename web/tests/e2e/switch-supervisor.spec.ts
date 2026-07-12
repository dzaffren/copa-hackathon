// E2E: switching to the supervisor view (Task 8) — "Switching to the supervisor
// view" (spec-drafter-workspace.md · Acceptance Criteria; Test 11). The strip's
// hand-off navigates to `/supervisor`, and the drafter workspace remains
// available to return to.
//
// Runs against the deterministic, offline `engineStub`. NOTE: authored for the
// E2E gate against the wired workspace; not run here (no browsers installed).

import { expect, test } from "@playwright/test";

import { installEngineStub } from "./fixtures/engineStub";

test.beforeEach(async ({ page }) => {
  await installEngineStub(page);
  await page.goto("/");
  await expect(page.getByTestId("node-rmit-v2-2026-draft")).toBeVisible();
});

test("clicking 'Switch to supervisor view' navigates to /supervisor", async ({
  page,
}) => {
  await page.getByRole("link", { name: "Switch to supervisor view" }).click();

  await expect(page).toHaveURL(/\/supervisor$/);
  await expect(
    page.getByRole("heading", { name: /supervisor view/i }),
  ).toBeVisible();
});

test("going back returns to the workspace with the cluster intact", async ({
  page,
}) => {
  await page.getByRole("link", { name: "Switch to supervisor view" }).click();
  await expect(page).toHaveURL(/\/supervisor$/);

  await page.goBack();

  // Back on the workspace: the draft anchors the still-intact cluster map and the
  // detail panel is auto-populated again (never blank).
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByTestId("node-rmit-v2-2026-draft")).toBeVisible();
  await expect(
    page.getByTestId("detail-panel").getByRole("button", {
      name: "Open the draft",
    }),
  ).toBeVisible();
});
