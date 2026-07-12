// E2E: node detail (Task 7) — "Inspecting my editable draft", "Clicking empty
// map space keeps the current detail", "Selecting a node after a connection
// returns to node detail" (spec-drafter-workspace.md · Acceptance Criteria).
//
// Runs against the deterministic, offline `engineStub` (the real technology-risk
// corpus) — no Python engine. Locators follow the spec's Locator strategies:
// `node-{id}`, `edge-{source}__{target}`, the `detail-panel` region, accessible
// action names, and the `why-this-changed` trail.

import { expect, test } from "@playwright/test";

import { installEngineStub } from "./fixtures/engineStub";

test.beforeEach(async ({ page }) => {
  await installEngineStub(page);
  await page.goto("/");
});

test("inspecting my editable draft shows status, version, linked-to, trail and Open the draft", async ({
  page,
}) => {
  const panel = page.getByTestId("detail-panel");
  await expect(panel).toHaveAttribute("role", "region");

  await page.getByTestId("node-rmit-v2-2026-draft").click();

  // Derived status + version.
  await expect(panel).toContainText("v2 · 2026 draft");
  await expect(panel).toContainText(/in progress/i);
  // "Linked to" list (hydrated from GET /nodes) names the connected policies.
  await expect(panel).toContainText(/Outsourcing/);
  await expect(panel).toContainText(/Operational Resilience/);
  // The "Why this changed" trail is present for the draft.
  await expect(panel.getByTestId("why-this-changed")).toBeVisible();
  // Exactly one enabled action for the single editable draft.
  await expect(
    panel.getByRole("button", { name: "Open the draft" }),
  ).toBeEnabled();
});

test("clicking empty map space keeps the current detail (never blank, no error)", async ({
  page,
}) => {
  const panel = page.getByTestId("detail-panel");
  await page.getByTestId("node-rmit-v2-2026-draft").click();
  await expect(
    panel.getByRole("button", { name: "Open the draft" }),
  ).toBeVisible();

  // Click empty canvas — the React Flow pane background, neither node nor edge.
  await page.locator(".react-flow__pane").click({ position: { x: 6, y: 6 } });

  // The RMiT v2 detail stays shown.
  await expect(
    panel.getByRole("button", { name: "Open the draft" }),
  ).toBeVisible();
});

test("selecting a node after a connection returns to node detail", async ({
  page,
}) => {
  const panel = page.getByTestId("detail-panel");

  // Select the core RMiT ↔ Outsourcing connection.
  await page
    .getByTestId("edge-rmit-v2-2026-draft__outsourcing-v1-2019")
    .click();
  await expect(
    panel.getByRole("heading", { name: /why these are connected/i }),
  ).toBeVisible();

  // Then select the Operational Resilience policy node.
  await page.getByTestId("node-opres-v1-2025-draft").click();

  // The panel switches back to node detail with a read-only action …
  await expect(panel.getByRole("button", { name: "Read-only" })).toBeVisible();
  // … and the connection explanation is no longer shown.
  await expect(
    panel.getByRole("heading", { name: /why these are connected/i }),
  ).toHaveCount(0);
});
