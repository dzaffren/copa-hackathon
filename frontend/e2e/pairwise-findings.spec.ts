import { test, expect, type Page } from "@playwright/test";
import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

/**
 * The Pairwise Findings box on the task page (spec Verification > E2E).
 *
 * Runs on `open-finance-pd-2026`, which is the only fixture that proves the
 * point: its task node has ONE edge, that pair has no findings at all, and all
 * 130 findings hang off edges between its neighbour and other documents. Before
 * this epic the box showed nothing here.
 *
 * Requires the FastAPI engine (:8000) and Vite (:5173) — see e2e/README.md. No
 * model credentials needed: the committed findings are read, not generated.
 *
 * WRITES TO TRACKED PATHS: accepting and dismissing persist review state into
 * data/workstreams/open-finance-pd-2026/findings/. Run
 * `afterEach` restores those files byte-for-byte from a snapshot, so no manual
 * cleanup is needed and nothing outside `findings/` is ever touched.
 */

const TASK_URL =
  "/workstreams/open-finance-pd-2026/tasks/open-finance-pd-2026-pd";

const LABELS = [
  "conflicts-with",
  "differs-on",
  "silent-on",
  "goes-beyond",
  "aligns-with",
];

function group(page: Page, label: string) {
  return page.locator(`[data-testid="finding-group"][data-label="${label}"]`);
}

function cards(page: Page) {
  return page.getByTestId("finding-card");
}

async function openTask(page: Page) {
  await page.goto(TASK_URL);
  await expect(group(page, "differs-on")).toBeVisible();
}

// Accepting and dismissing write review state into the tracked findings files,
// so without a reset the specs only pass in one order on a clean tree.
//
// This used to run `git checkout -- data/workstreams/<ws>`, which was safe only
// while the fixture held no uncommitted work. It does now — the demo carries the
// drafter's accepted findings, `source_pdf` fields on the graph, and a directory
// rename — and that command silently destroyed all of it during development of
// the Recommendations feature.
//
// Snapshot-and-restore instead: only the findings files this spec can write are
// captured, and they are put back byte-for-byte. It cannot reach anything else in
// the workstream, committed or not.
const FINDINGS_DIR = path.resolve(
  process.cwd(),
  "..",
  "data/workstreams/open-finance-pd-2026/findings",
);

let snapshot: Map<string, Buffer>;

test.beforeEach(() => {
  snapshot = new Map(
    readdirSync(FINDINGS_DIR)
      .filter((name) => name.endsWith(".json"))
      .map((name) => [name, readFileSync(path.join(FINDINGS_DIR, name))]),
  );
});

test.afterEach(() => {
  for (const [name, bytes] of snapshot) {
    writeFileSync(path.join(FINDINGS_DIR, name), bytes);
  }
});

test.describe("Pairwise Findings box", () => {
  test("is populated even though the working draft is blank", async ({
    page,
  }) => {
    await openTask(page);

    // The retired empty-draft gate would have replaced all of this with a
    // "no findings until the draft has content" message.
    const box = page.getByTestId("pairwise-card");
    await expect(
      box.getByRole("heading", { name: "Pairwise findings" }),
    ).toBeVisible();
    await expect(
      box.getByText(
        /Semantic linkages \(differs-on, conflicts-with, silent-on, aligns-with, goes-beyond\) between nodes/,
      ),
    ).toBeVisible();
    await expect(box).not.toContainText(/until the draft has content/i);
    await expect(cards(page)).toHaveCount(130);
  });

  test("draws findings from documents two steps from the draft", async ({
    page,
  }) => {
    await openTask(page);

    // None of these pairs involves the task document. All three were invisible
    // on this screen before the widening. `data-edge-id` is on the card itself,
    // so this is an attribute filter, not a descendant filter.
    const perEdge: Record<string, number> = {
      "e-rmit_2025--ed_open_finance_2025": 51,
      "e-hkma_open_api_framework--ed_open_finance_2025": 47,
      "e-bis_papers_168--ed_open_finance_2025": 32,
    };
    for (const [edgeId, count] of Object.entries(perEdge)) {
      await expect(
        page.locator(`[data-testid="finding-card"][data-edge-id="${edgeId}"]`),
      ).toHaveCount(count);
    }

    // Exact match: "Documents" also occurs inside finding summaries.
    await expect(page.getByText("Documents", { exact: true })).toBeVisible();
    await expect(page.getByText("3 of 5", { exact: true })).toBeVisible();
  });

  test("groups by label in attention order, with honest counts", async ({
    page,
  }) => {
    await openTask(page);

    const rendered = await page
      .getByTestId("finding-group")
      .evaluateAll((els) => els.map((e) => e.getAttribute("data-label")));
    expect(rendered).toEqual(LABELS);

    await expect(
      group(page, "differs-on").getByTestId("group-total"),
    ).toHaveText("30");
    await expect(
      group(page, "aligns-with").getByTestId("group-total"),
    ).toHaveText("75");
    // Every card renders — no "show all" hiding any of the 75 alignments.
    await expect(
      group(page, "aligns-with").getByTestId("finding-card"),
    ).toHaveCount(75);
    await expect(page.getByRole("button", { name: /show all/i })).toHaveCount(
      0,
    );
  });

  test("shows an empty group as a zero rather than hiding it", async ({
    page,
  }) => {
    await openTask(page);

    // This fixture genuinely has no conflicts. "0 conflicts" and "conflicts not
    // checked" must not look the same.
    const conflicts = group(page, "conflicts-with");
    await expect(conflicts.getByTestId("group-total")).toHaveText("0");
    await expect(conflicts.getByTestId("group-empty")).toHaveText(
      "None found.",
    );
  });

  test("accepting sinks the card within its own group", async ({ page }) => {
    await openTask(page);

    const differs = group(page, "differs-on");
    const pendingBefore = Number(
      await differs.getByTestId("group-pending").innerText(),
    );
    const first = differs
      .locator('[data-testid="finding-card"][data-review-state="pending"]')
      .first();
    const findingId = await first.getAttribute("data-finding-id");

    await first.getByRole("button", { name: /Accept/ }).click();

    const accepted = differs.locator(`[data-finding-id="${findingId}"]`);
    await expect(accepted).toHaveAttribute("data-review-state", "accepted");

    // Still in differs-on, now last, and the group total has not moved. Pending
    // is asserted as a DELTA: the demo fixture ships with real acceptances, so
    // "30 minus one" only held while a destructive reset emptied it first.
    await expect(differs.getByTestId("group-total")).toHaveText("30");
    await expect(differs.getByTestId("group-pending")).toHaveText(
      String(pendingBefore - 1),
    );
    // The property is that it SANK below every still-pending card — not that it
    // is strictly last. The fixture already holds accepted findings in this
    // group, so a newly accepted one joins them rather than going to the end.
    const states = await differs
      .getByTestId("finding-card")
      .evaluateAll((els) =>
        els.map((e) => ({
          id: e.getAttribute("data-finding-id"),
          state: e.getAttribute("data-review-state"),
        })),
      );
    expect(states).toHaveLength(30);
    const movedTo = states.findIndex((c) => c.id === findingId);
    const lastPending = states.reduce(
      (acc, c, i) => (c.state === "pending" ? i : acc),
      -1,
    );
    expect(movedTo).toBeGreaterThan(lastPending);
  });

  test("undo returns a judged finding to pending", async ({ page }) => {
    await openTask(page);

    const aligns = group(page, "aligns-with");
    // Deltas, not absolutes: the demo fixture ships with real acceptances, so a
    // hard-coded "74 then 75" only held while a destructive reset emptied it.
    const pendingBefore = Number(
      await aligns.getByTestId("group-pending").innerText(),
    );
    const first = aligns
      .locator('[data-testid="finding-card"][data-review-state="pending"]')
      .first();
    const findingId = await first.getAttribute("data-finding-id");

    await first.getByRole("button", { name: /Dismiss/ }).click();
    const card = aligns.locator(`[data-finding-id="${findingId}"]`);
    await expect(card).toHaveAttribute("data-review-state", "dismissed");
    await expect(aligns.getByTestId("group-pending")).toHaveText(
      String(pendingBefore - 1),
    );

    await card.getByRole("button", { name: /Undo/ }).click();
    await expect(card).toHaveAttribute("data-review-state", "pending");
    await expect(aligns.getByTestId("group-pending")).toHaveText(
      String(pendingBefore),
    );
  });

  test("Review opens the comparison on the finding that was clicked", async ({
    page,
  }) => {
    await openTask(page);

    const card = group(page, "differs-on").getByTestId("finding-card").first();
    const findingId = await card.getAttribute("data-finding-id");
    const summary = await card.locator("p").first().innerText();

    await card.getByRole("button", { name: "Review" }).click();

    await expect(page).toHaveURL(
      new RegExp(
        `/edges/.+/review\\?finding=${encodeURIComponent(findingId!)}`,
      ),
    );
    // The nominated finding is the selected one, not the pair's first.
    const active = page.locator(
      '[data-testid="finding-card"][data-active="true"]',
    );
    await expect(active).toContainText(summary.slice(0, 40));
  });

  test("filters by several documents at once", async ({ page }) => {
    await openTask(page);
    const filter = page.getByRole("group", { name: "Filter by node" });

    const rmit = filter.getByRole("button", { name: /^RMiT/ });
    const hkma = filter.getByRole("button", { name: /^HKMA/ });

    await rmit.click();
    await hkma.click();
    await expect(rmit).toHaveAttribute("aria-pressed", "true");
    await expect(hkma).toHaveAttribute("aria-pressed", "true");

    // 51 RMiT + 47 HKMA, and no BIS.
    await expect(cards(page)).toHaveCount(98);
    await expect(
      cards(page).filter({
        has: page.locator(
          '[data-edge-id="e-bis_papers_168--ed_open_finance_2025"]',
        ),
      }),
    ).toHaveCount(0);

    // Deselecting one leaves the other selected.
    await rmit.click();
    await expect(hkma).toHaveAttribute("aria-pressed", "true");
    await expect(cards(page)).toHaveCount(47);

    await filter.getByRole("button", { name: "All" }).click();
    await expect(cards(page)).toHaveCount(130);
  });

  test("names the pairs that have never been analysed", async ({ page }) => {
    await openTask(page);

    // Grouping by label means a findings-free pair contributes no card, so the
    // coverage gap needs its own home or it disappears silently.
    const strip = page.getByTestId("coverage-strip");
    await expect(strip).toBeVisible();
    await expect(strip.getByTestId("coverage-pair")).toHaveCount(2);
    await expect(
      strip.locator(
        '[data-edge-id="e-abs_mas_api_playbook--ed_open_finance_2025"]',
      ),
    ).toBeVisible();
    await expect(
      strip.locator(
        '[data-edge-id="e-open_finance_pd_2026_pd--ed_open_finance_2025"]',
      ),
    ).toBeVisible();
    await expect(
      strip.getByRole("button", { name: /Analyze/ }).first(),
    ).toBeEnabled();
  });
});
