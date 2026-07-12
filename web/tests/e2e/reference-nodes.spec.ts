// E2E: external-reference nodes (Task 7) — "An external reference node shows
// that it exists and why it matters", "The deep reference content is deferred to
// the Reference Radar", "The Regulatory Handbook reference is a locked,
// content-withheld placeholder" (spec-drafter-workspace.md · Acceptance Criteria).
//
// The reference band is client-side overlay (workspaceOverlay) merged onto the
// engine graph, so these nodes render even though the offline `engineStub` serves
// only the policy corpus. The workspace shows THAT a reference exists, that it
// connects, and a short "why it matters" — never the verbatim, clause-by-clause
// passages (those are the Reference Radar's, #26).

import { expect, test } from "@playwright/test";

import { installEngineStub } from "./fixtures/engineStub";

test.beforeEach(async ({ page }) => {
  await installEngineStub(page);
  await page.goto("/");
});

test("a public reference node shows why-it-matters + a Reference Radar hand-off, no verbatim passage", async ({
  page,
}) => {
  const panel = page.getByTestId("detail-panel");

  await page.getByTestId("node-pdpa-2010").click();

  await expect(panel).toContainText(/why this reference matters/i);
  await expect(panel).toContainText(/personal data/i);
  // The hand-off to the Reference Radar (#26) for the verbatim detail …
  await expect(
    panel.getByRole("button", { name: "See in the Reference Radar" }),
  ).toBeVisible();
  // … and the deep content is deferred, not shown here.
  await expect(panel).toContainText(/reference radar/i);
  await expect(panel).toContainText(/not shown here/i);
  await expect(panel.getByTestId("clause-passage")).toHaveCount(0);
});

test("the Regulatory Handbook reference is a locked, content-withheld placeholder", async ({
  page,
}) => {
  const panel = page.getByTestId("detail-panel");

  await page.getByTestId("node-bnm-handbook").click();

  // Connects to the draft, but restricted and content-withheld …
  await expect(panel).toContainText(/restricted/i);
  await expect(panel).toContainText(/withheld/i);
  // … the only action is disabled, and there is NO Reference Radar hand-off.
  await expect(
    panel.getByRole("button", { name: "Restricted" }),
  ).toBeDisabled();
  await expect(
    panel.getByRole("button", { name: "See in the Reference Radar" }),
  ).toHaveCount(0);
  // No verbatim clause is ever fetched or rendered for a withheld reference.
  await expect(panel.getByTestId("clause-passage")).toHaveCount(0);
});
