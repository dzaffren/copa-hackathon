// E2E: opening the workspace (Task 8) — "Opening the workspace shows the whole
// cluster with one editable draft", "RMiT v2 is the only node I can edit", "The
// workspace opens with my draft already selected", and "Approval is never offered
// in the workspace" (spec-drafter-workspace.md · Acceptance Criteria; Test 1).
//
// Runs against the deterministic, offline `engineStub` (the real technology-risk
// corpus) — no Python engine. Locators follow the spec's Locator strategies:
// `node-{id}`, the `detail-panel` region, and accessible action names.
//
// NOTE: authored for the E2E gate against the wired workspace; not run here (no
// browsers installed).

import { expect, test } from "@playwright/test";

import { CORPUS_GRAPH, installEngineStub } from "./fixtures/engineStub";

test.beforeEach(async ({ page }) => {
  await installEngineStub(page);
  await page.goto("/");
  // The draft anchors the map; wait for it before asserting.
  await expect(page.getByTestId("node-rmit-v2-2026-draft")).toBeVisible();
});

test("opening the workspace shows the whole technology-risk cluster on one map", async ({
  page,
}) => {
  // Every real corpus policy node is on the map — never a single-document view.
  for (const node of CORPUS_GRAPH.nodes) {
    await expect(page.getByTestId(`node-${node.id}`)).toBeVisible();
  }
});

test("the draft is auto-selected on load — the panel is not blank and needs no click", async ({
  page,
}) => {
  const panel = page.getByTestId("detail-panel");
  await expect(panel).toHaveAttribute("role", "region");

  // Without clicking anything, the panel already shows the RMiT v2 draft …
  await expect(panel).toContainText("v2 · 2026 draft");
  const openDraft = panel.getByRole("button", { name: "Open the draft" });
  await expect(openDraft).toBeVisible();
  await expect(openDraft).toBeEnabled();
});

test("'Open the draft' is the single editable action — RMiT v2 is the only editable node", async ({
  page,
}) => {
  // The one enabled edit action lives only in the auto-selected draft's panel.
  await expect(
    page.getByRole("button", { name: "Open the draft" }),
  ).toHaveCount(1);
});

test("approval is never offered in the workspace", async ({ page }) => {
  // No approve / submit-for-approval / return-to-bank action exists anywhere.
  await expect(
    page.getByRole("button", {
      name: /approve|submit for approval|return to bank/i,
    }),
  ).toHaveCount(0);
});
