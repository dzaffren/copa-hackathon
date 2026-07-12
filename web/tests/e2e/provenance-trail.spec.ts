// E2E: the "Why this changed" trail (Task 7) — "The 'Why this changed' trail
// lists public supporting documents", "An internal supporting document appears
// locked and content-withheld", "Provenance lives in the detail panel, never on
// the map" (spec-drafter-workspace.md · Acceptance Criteria; Test 9).
//
// The trail is client-side (provenance.ts), rendered only inside the detail panel
// when the draft is selected — supporting documents are NEVER their own graph
// nodes. Public entries show title + date; the internal committee minutes are
// listed but restricted, with their content withheld.

import { expect, test } from "@playwright/test";

import { installEngineStub } from "./fixtures/engineStub";

test.beforeEach(async ({ page }) => {
  await installEngineStub(page);
  await page.goto("/");
});

test("the trail lists public docs with titles + dates and locks the internal one", async ({
  page,
}) => {
  const panel = page.getByTestId("detail-panel");
  await page.getByTestId("node-rmit-v2-2026-draft").click();

  const trail = panel.getByTestId("why-this-changed");
  await expect(trail).toBeVisible();

  // Public supporting documents — real title + date shown.
  await expect(trail).toContainText(
    "Operational Resilience — Discussion Paper",
  );
  await expect(trail).toContainText("19 Dec 2025");
  await expect(trail).toContainText("RMiT FAQs (updated)");
  await expect(trail).toContainText("1 Jul 2026");

  // The internal document — listed so the trail stays complete, but withheld.
  const internal = trail.getByTestId(
    "provenance-prov-jpp-minutes-cloud-review",
  );
  await expect(internal).toContainText(
    "JPP Committee minutes — cloud policy review",
  );
  await expect(internal).toContainText(/restricted/i);
  await expect(internal).toContainText(/content withheld/i);
});

test("supporting documents never appear as their own graph nodes", async ({
  page,
}) => {
  await page.getByTestId("node-rmit-v2-2026-draft").click();

  // The provenance docs live only inside the trail — never as React Flow nodes.
  await expect(
    page.locator(".react-flow__node", { hasText: "RMiT FAQs" }),
  ).toHaveCount(0);
  await expect(
    page.locator(".react-flow__node", { hasText: "JPP Committee minutes" }),
  ).toHaveCount(0);
  // (No node testid exists for any provenance entry either.)
  await expect(page.locator('[data-testid^="node-prov-"]')).toHaveCount(0);
});
