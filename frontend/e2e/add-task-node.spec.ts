import { test, expect, type Page } from "@playwright/test";

// E2E for the shared task-type vocabulary on add-node (spec-shared-task-type.md,
// Verification > E2E).
// Requires the FastAPI engine and the Vite app running — see e2e/README.md.
//
// Why these three scenarios are here and not in Vitest: the happy path adds a
// working draft through the real multipart upload, and a FormData `fetch` never
// resolves under MSW v2 + jsdom, so the component suite
// (src/features/workstream-graph/AddNodeDialog.test.tsx) stops at the
// `createNode` call. The two negative scenarios ride along on the same real
// stack so the "no kind, no submit" rule and the clear-on-switch rule are
// pinned in front of the server that also enforces them (TASK_TYPE_REQUIRED /
// TASK_TYPE_NOT_ALLOWED) rather than in front of a mock.
//
// NOTE: the run adds a node to the open-finance-pd-2026 fixture, which is a
// tracked path — `git checkout data/workstreams/open-finance-pd-2026` after a
// local run, and delete the untracked `anchors/` and `sources/` files the run
// leaves behind for the new node.

const DECK_TITLE = "Open Finance Industry Engagement Deck 2026";

// The existing working draft — the edge target every scenario links to. Selected
// by option value (the node id) rather than by label: `selectOption` takes a
// plain string, not a regex. `references` is used throughout because
// `contributes-to` was retired on 29 Jul 2026 and the server refuses it on write.
const DRAFT_ID = "open-finance-pd-2026-pd";
const DRAFT_TITLE = "Open Finance PD . 2026 (PD)";

// Every document in this workstream hangs off the published ED, so it is the
// one node from which any other is one neighbour-chip away.
const HUB_TITLE = "ED Open Finance 2025";

/** Attach a small numbered-paragraph PDF the semi-structured segmenter can walk. */
async function attachDeck(page: Page) {
  await page.getByLabel("Attachment").setInputFiles({
    name: "open-finance-engagement-deck.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from(
      "# Open Finance industry engagement\n\n" +
        "1.1 The Bank will convene industry participants to discuss the scope " +
        "of consented data sharing under the proposed open finance framework.\n\n" +
        "1.2 Participants are invited to comment on the proposed API " +
        "standards and the phased implementation timeline.\n",
    ),
  });
}

/** True when the right rail is showing a node (rather than an edge or the idle
 *  cross-workstream rail) — the node panel is the only one with this heading. */
function nodePanelOpen(page: Page) {
  return page
    .getByText("First-order neighbours", { exact: true })
    .isVisible()
    .catch(() => false);
}

/**
 * Open a node's detail panel by title.
 *
 * The graph is drawn by react-force-graph-2d into a single `<canvas>`, so in the
 * real browser there is no per-node DOM element to click — the accessible
 * one-button-per-node DOM only exists in the Vitest stub
 * (src/test/mocks/react-force-graph-2d.tsx). The only DOM handles on a node are
 * the panel's neighbour chips, so this sweeps the canvas until *some* node
 * opens, hops to the hub, and clicks the wanted node's chip.
 */
async function openNode(page: Page, title: string) {
  const canvas = page.getByTestId("graph-canvas");
  await canvas.waitFor();
  const heading = page.locator("h2").first();

  if (!(await nodePanelOpen(page))) {
    const box = (await canvas.boundingBox())!;
    // Node radii are 8px (anchor) / 13px (task), so a 12px stride cannot skip one.
    sweep: for (let y = box.y + 6; y < box.y + box.height - 6; y += 12) {
      for (let x = box.x + 6; x < box.x + box.width - 6; x += 12) {
        await page.mouse.click(x, y);
        if (await nodePanelOpen(page)) break sweep;
      }
    }
    expect(
      await nodePanelOpen(page),
      "swept the canvas without opening any node",
    ).toBe(true);
  }

  if ((await heading.textContent())?.trim() === title) return;

  if ((await heading.textContent())?.trim() !== HUB_TITLE) {
    await page.getByRole("button", { name: HUB_TITLE }).first().click();
    await expect(heading).toHaveText(HUB_TITLE);
  }
  await page.getByRole("button", { name: title }).first().click();
  await expect(heading).toHaveText(title);
}

test.describe("Add a working draft with a deliverable kind", () => {
  // The canvas sweep plus a real chunking upload needs more than the 30s default.
  test.setTimeout(180_000);

  test("classify as a working draft, pick Engagement Deck, see the chip", async ({
    page,
  }) => {
    await page.goto("/workstreams/open-finance-pd-2026");
    await page.getByTestId("graph-canvas").waitFor();

    await page.getByRole("button", { name: /add node/i }).click();

    // Classifying it as a working draft is what raises the deliverable-kind
    // question — the grid does not exist for a context document.
    await page.getByRole("radio", { name: "task" }).click();
    const taskTypes = page.getByRole("radiogroup", { name: "Task type" });
    await expect(taskTypes).toBeVisible();
    await expect(taskTypes.getByRole("radio")).toHaveCount(8);

    // The radio's accessible name is the CODE; its visible text is the
    // drafter-facing label.
    const deck = taskTypes.getByRole("radio", { name: "DECK" });
    await expect(deck).toHaveText(/Engagement Deck/);
    await deck.click();
    await expect(deck).toBeChecked();

    await page.getByLabel("Title").fill(DECK_TITLE);
    await page
      .getByLabel("Description")
      .fill("Slides for the 2026 open finance industry engagement session.");
    await attachDeck(page);

    await page.getByRole("button", { name: /add edge/i }).click();
    await page.getByLabel("Edge 1 target").selectOption(DRAFT_ID);
    await page.getByLabel("Edge 1 type").selectOption("references");

    const submit = page.getByRole("button", { name: /add to graph/i });
    await expect(submit).toBeEnabled();
    await submit.click();

    // The dialog closes once the server has chunked and stored the node.
    await expect(submit).toHaveCount(0, { timeout: 120_000 });

    // It has joined the graph the canvas draws: the working draft it was linked
    // to now lists it as a first-order neighbour.
    await openNode(page, DRAFT_TITLE);
    const newNode = page.getByRole("button", { name: DECK_TITLE });
    await expect(newNode).toBeVisible();

    // Opening it shows the deliverable kind as its human label, not the code.
    await newNode.click();
    await expect(page.locator("h2").first()).toHaveText(DECK_TITLE);
    await expect(page.getByTestId("task-type-chip")).toHaveText(
      "Engagement Deck",
    );
  });

  test("a working draft cannot be added without a deliverable kind", async ({
    page,
  }) => {
    await page.goto("/workstreams/open-finance-pd-2026");
    await page.getByTestId("graph-canvas").waitFor();

    await page.getByRole("button", { name: /add node/i }).click();

    await page.getByRole("radio", { name: "task" }).click();
    const taskTypes = page.getByRole("radiogroup", { name: "Task type" });
    await expect(taskTypes).toBeVisible();

    // Everything else the form asks for is supplied — title, attachment, and a
    // complete edge row — so the deliverable kind is the only thing missing.
    await page.getByLabel("Title").fill("Untyped working draft");
    await attachDeck(page);
    await page.getByRole("button", { name: /add edge/i }).click();
    await page.getByLabel("Edge 1 target").selectOption(DRAFT_ID);
    await page.getByLabel("Edge 1 type").selectOption("references");

    // Nothing is picked, so the graph stays closed to it.
    await expect(taskTypes.getByRole("radio", { checked: true })).toHaveCount(
      0,
    );
    await expect(
      page.getByRole("button", { name: /add to graph/i }),
    ).toBeDisabled();
  });

  test("switching classification away from a working draft drops the question", async ({
    page,
  }) => {
    await page.goto("/workstreams/open-finance-pd-2026");
    await page.getByTestId("graph-canvas").waitFor();

    await page.getByRole("button", { name: /add node/i }).click();

    await page.getByRole("radio", { name: "task" }).click();
    const taskTypes = page.getByRole("radiogroup", { name: "Task type" });
    await taskTypes.getByRole("radio", { name: "FAQ" }).click();
    await expect(taskTypes.getByRole("radio", { name: "FAQ" })).toBeChecked();

    // Reclassifying as a context document retires the question entirely — a
    // stale pick must never reach the server, which refuses it.
    await page.getByRole("radio", { name: "international-standard" }).click();
    await expect(
      page.getByRole("radiogroup", { name: "Task type" }),
    ).toHaveCount(0);

    // And it can be added to the graph without one.
    await page
      .getByLabel("Title")
      .fill("Context document, no deliverable kind");
    await attachDeck(page);
    await page.getByRole("button", { name: /add edge/i }).click();
    await page.getByLabel("Edge 1 target").selectOption(DRAFT_ID);
    await page.getByLabel("Edge 1 type").selectOption("references");

    await expect(
      page.getByRole("button", { name: /add to graph/i }),
    ).toBeEnabled();
  });
});
