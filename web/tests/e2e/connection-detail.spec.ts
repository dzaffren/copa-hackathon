// E2E: connection detail (Task 7) — "Understanding the core cluster connection"
// and "A different connection shows a different real overlap"
// (spec-drafter-workspace.md · Acceptance Criteria; Tests 3–4).
//
// Every quote is the verbatim clause text the engine returns for its number
// (served here by the offline `engineStub`), upholding the verbatim-citation
// guardrail — and the corrected overlap cites the real `Operational Resilience
// 1.1`, never the phantom `6.11`.

import { expect, test } from "@playwright/test";

import { installEngineStub } from "./fixtures/engineStub";

test.beforeEach(async ({ page }) => {
  await installEngineStub(page);
  await page.goto("/");
});

test("the core RMiT ↔ Outsourcing connection quotes Outsourcing 12.1 verbatim", async ({
  page,
}) => {
  const panel = page.getByTestId("detail-panel");

  await page
    .getByTestId("edge-rmit-v2-2026-draft__outsourcing-v1-2019")
    .click();

  await expect(
    panel.getByRole("heading", { name: /why these are connected/i }),
  ).toBeVisible();
  // The cited clause number …
  await expect(panel).toContainText("Outsourcing 12.1");
  // … and its verbatim text (exactly as returned by GET /clauses).
  await expect(panel).toContainText(
    "A financial institution must obtain the Bank's written approval before " +
      "entering into a new material outsourcing arrangement.",
  );
});

test("a different connection (RMiT ↔ Operational Resilience) cites its own clause, never 6.11", async ({
  page,
}) => {
  const panel = page.getByTestId("detail-panel");

  await page
    .getByTestId("edge-rmit-v2-2026-draft__opres-v1-2025-draft")
    .click();

  // Cites RMiT 10.50 overlapping Operational Resilience 1.1 …
  await expect(panel).toContainText("RMiT 10.50");
  await expect(panel).toContainText("Operational Resilience 1.1");
  // … with the verbatim OpRes 1.1 text hydrated by number …
  await expect(panel).toContainText(
    /continuity of critical financial services/i,
  );
  // … and never the phantom clause the spec corrected away.
  await expect(panel).not.toContainText("6.11");
});
