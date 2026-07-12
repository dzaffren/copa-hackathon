// E2E: preview / cross-cluster nodes are labelled, non-actionable previews
// (spec-drafter-workspace.md · Verification → E2E table, Task 6 rows: "The
// AML/CFT cross-cluster node is preview only", "The trend and news signals are a
// labelled preview").
//
// Both nodes come from the client-side overlay (`workspaceOverlay.ts`). On the
// map they must read as previews that cannot be acted on: the derived marking
// says so, and the node carries a non-actionable affordance (aria-disabled /
// data-disabled) — the disabled action label itself lives in the detail panel
// (Task 7).
//
// NOTE: authored for the E2E gate against the wired workspace (Task 8); not run
// here (no browsers installed).

import { expect, test } from "@playwright/test";

import { installEngineStub } from "./fixtures/engineStub";

test.describe("Cluster map — preview & cross-cluster nodes", () => {
  test.beforeEach(async ({ page }) => {
    await installEngineStub(page);
    await page.goto("/");
    await expect(page.getByTestId("node-rmit-v2-2026-draft")).toBeVisible();
  });

  test("the AML/CFT cross-cluster node is a labelled preview only", async ({
    page,
  }) => {
    const aml = page.getByTestId("node-aml-cft");
    await expect(aml).toBeVisible();
    await expect(aml).toHaveAttribute(
      "data-marking",
      "other cluster (preview only)",
    );
    await expect(aml).toHaveAttribute("data-treatment", "cross-cluster");
    // Non-actionable on the map — cannot be opened.
    await expect(aml).toHaveAttribute("aria-disabled", "true");
    await expect(aml).toHaveAttribute("data-disabled", "true");
  });

  test("the trend / news signal node is a labelled preview", async ({
    page,
  }) => {
    const trend = page.getByTestId("node-trend-cloud-signals");
    await expect(trend).toBeVisible();
    await expect(trend).toHaveAttribute(
      "data-marking",
      "external signal · preview",
    );
    await expect(trend).toHaveAttribute("data-treatment", "reference-preview");
    await expect(trend).toHaveAttribute("aria-disabled", "true");
    await expect(trend).toHaveAttribute("data-disabled", "true");
  });

  test("neither preview node is editable or offers an action on the map", async ({
    page,
  }) => {
    for (const id of ["aml-cft", "trend-cloud-signals"]) {
      const node = page.getByTestId(`node-${id}`);
      await expect(node).toHaveAttribute("data-disabled", "true");
      await expect(node).not.toHaveAttribute(
        "data-marking",
        "your draft — you edit",
      );
    }
  });
});
