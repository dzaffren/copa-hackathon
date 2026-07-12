// E2E: node markings on the cluster map (spec-drafter-workspace.md · Verification
// → E2E table, Task 6 rows: "Each node's marking matches its derived treatment",
// "Node status is derived, never set by hand", "Published BNM policies offer no
// editing action").
//
// The map is a pure read client of the engine; `installEngineStub` serves the
// REAL technology-risk corpus offline. Expectations are DRIVEN FROM the same
// `treatments.ts` the app uses (via `deriveMarking` over the mapped model), so a
// change to a marking string can never silently diverge from the test.
//
// NOTE: these specs target the wired workspace (Task 8) and run at the E2E gate
// (browsers installed there); they are authored here, not executed now.

import { expect, test } from "@playwright/test";

import { CORPUS_GRAPH, installEngineStub } from "./fixtures/engineStub";
import { workspaceOverlay } from "../../src/fixtures/workspaceOverlay";
import { toReactFlowModel } from "../../src/lib/graphModel";
import { deriveMarking } from "../../src/lib/treatments";

test.describe("Cluster map — node markings match derived treatments", () => {
  test.beforeEach(async ({ page }) => {
    await installEngineStub(page);
    await page.goto("/");
    // The draft anchors the map; wait for it before asserting.
    await expect(page.getByTestId("node-rmit-v2-2026-draft")).toBeVisible();
  });

  test("every rendered node's data-marking equals what treatments.ts derives", async ({
    page,
  }) => {
    const model = toReactFlowModel(CORPUS_GRAPH, workspaceOverlay);
    for (const node of model.nodes) {
      await expect(page.getByTestId(node.data.testId)).toHaveAttribute(
        "data-marking",
        deriveMarking(node.data.node),
      );
    }
  });

  test("the real corpus nodes carry their exact contractual markings", async ({
    page,
  }) => {
    // opres-v1-2025-draft is In-progress in the corpus but is BNM's published
    // discussion paper — so "published · draft (read-only)", NOT "in force".
    const expected: Record<string, string> = {
      "node-rmit-v2-2026-draft": "your draft — you edit",
      "node-rmit-v1-2020": "published · superseded (read-only history)",
      "node-outsourcing-v1-2019": "published · in force (read-only)",
      "node-opres-v1-2025-draft": "published · draft (read-only)",
      "node-aml-cft": "other cluster (preview only)",
      "node-bnm-handbook": "external reference · restricted (locked)",
      "node-trend-cloud-signals": "external signal · preview",
    };
    for (const [testId, marking] of Object.entries(expected)) {
      await expect(page.getByTestId(testId)).toHaveAttribute(
        "data-marking",
        marking,
      );
    }
  });

  test("exactly one node is the editable draft — status is derived, not hand-set", async ({
    page,
  }) => {
    const editable = page.locator('[data-marking="your draft — you edit"]');
    await expect(editable).toHaveCount(1);
    await expect(editable).toHaveAttribute(
      "data-testid",
      "node-rmit-v2-2026-draft",
    );

    // No control anywhere lets a drafter set or change a node's status.
    await expect(
      page.getByRole("button", { name: /set status|change status|mark as/i }),
    ).toHaveCount(0);
    await expect(page.getByRole("combobox", { name: /status/i })).toHaveCount(
      0,
    );
  });

  test("published BNM policies are all read-only (no editable marking)", async ({
    page,
  }) => {
    const publishedPolicyIds = [
      "rmit-v1-2020",
      "outsourcing-v1-2019",
      "bcm-v1-2022",
      "opres-v1-2025-draft",
      "recovery-planning-v1-2021",
      "customer-info-v1-2025",
    ];
    for (const id of publishedPolicyIds) {
      const node = page.getByTestId(`node-${id}`);
      await expect(node).toHaveAttribute("data-marking", /read-only/);
      await expect(node).not.toHaveAttribute(
        "data-marking",
        "your draft — you edit",
      );
    }
  });
});
