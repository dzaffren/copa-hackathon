import { test, expect, type Page } from "@playwright/test";
import path from "node:path";

/**
 * Builds the "Open Finance PD . 2026" workstream end to end THROUGH THE UI —
 * the whole epic exercised as a drafter would: create the workstream, add three
 * chunked documents, wire the graph, extract concepts, analyse a linkage.
 *
 * Graph shape:
 *   Open Finance PD (focal task)
 *     └── ED Open Finance 2025            (internal-published, semi-structured)
 *           ├── HKMA Open API Framework   (peer-regulator,    semi-structured)
 *           └── BIS Papers 168            (international-standard, prose)
 *
 * Requires the FastAPI engine (:8000) and Vite (:5173) running, plus live model
 * credentials — extraction and analysis make real model calls.
 *
 * WRITES TO TRACKED PATHS: creates data/workstreams/open-finance-pd-2026/.
 * Remove that directory after a run.
 */

// Playwright runs with cwd = frontend/ (where the config lives); the corpus sits
// one level up. `__dirname` is unavailable — the specs are ES modules.
const CORPUS = path.resolve(process.cwd(), "../data/corpus/open-finance");

const ED = "ED Open Finance 2025";
const HKMA = "HKMA Open API Framework";
const BIS = "BIS Papers 168";

async function addDocument(
  page: Page,
  opts: {
    nodeType: string;
    title: string;
    file: string;
    docClass: string;
    connectTo: string;
    edgeType: string;
  },
) {
  await page.getByRole("button", { name: /add node/i }).click();

  await page.getByRole("radio", { name: opts.nodeType }).click();
  await page.getByLabel("Title").fill(opts.title);
  await page
    .getByLabel("Attachment")
    .setInputFiles(path.join(CORPUS, opts.file));
  await page
    .getByRole("radiogroup", { name: "Breaking-up method" })
    .getByRole("radio", { name: opts.docClass })
    .click();

  await page.getByRole("button", { name: /add edge/i }).click();
  await page
    .getByLabel("Edge 1 target")
    .selectOption({ label: opts.connectTo });
  await page.getByLabel("Edge 1 type").selectOption(opts.edgeType);

  const submit = page.getByRole("button", { name: /add to graph/i });
  await expect(submit).toBeEnabled();
  await submit.click();

  // Ingest + chunking is a real round-trip through Document Intelligence.
  await expect(
    page.getByRole("button", { name: opts.title, exact: true }),
  ).toBeVisible({ timeout: 180_000 });
}

test("build Open Finance PD . 2026 from scratch and analyse a linkage", async ({
  page,
}) => {
  test.setTimeout(900_000); // real ingest + extraction + analysis

  // --- 1. Create the workstream; it opens on its focal task node ------------
  await page.goto("/workstreams/new");
  await page.getByLabel("Workstream name").fill("Open Finance PD . 2026");
  await page
    .getByLabel("Short description")
    .fill("PD serving as a foundational framework to facilitate consent-driven sharing of customer information across the financial sector in a secure, open, accessible, interoperable and timely manner.");
  await page.getByLabel("Deliverable type").selectOption("PD");
  await page.getByLabel("Target publication").fill("Q4 2026");
  await page.getByRole("button", { name: /create workstream/i }).click();

  await page.waitForURL(/\/workstreams\/open-finance-pd-2026/, {
    timeout: 30_000,
  });
  // The focal node is on the canvas — the anchor the first document attaches to.
  const focal = page.getByRole("button", { name: /Open Finance PD \. 2026/ });
  await expect(focal.first()).toBeVisible({ timeout: 30_000 });

  // --- 2. ED Open Finance 2025 → the focal node ----------------------------
  await addDocument(page, {
    nodeType: "internal-published",
    title: ED,
    file: "ED_Open_Finance_2025.pdf",
    docClass: "semi-structured",
    connectTo: "Open Finance PD . 2026 (PD)",
    edgeType: "references",
  });

  // --- 3. HKMA + BIS → the ED node -----------------------------------------
  await addDocument(page, {
    nodeType: "peer-regulator",
    title: HKMA,
    file: "hkma-20180718e5a2.pdf",
    docClass: "semi-structured",
    connectTo: ED,
    edgeType: "references",
  });

  await addDocument(page, {
    nodeType: "international-standard",
    title: BIS,
    file: "bispap168.pdf",
    docClass: "prose",
    connectTo: ED,
    edgeType: "references",
  });

  // Four nodes on the canvas: focal + three documents.
  await expect(page.locator("svg circle")).toHaveCount(4);

  // --- 4. Extract concepts on the ED node ----------------------------------
  await page.getByRole("button", { name: ED, exact: true }).click();
  const extract = page.getByRole("button", { name: /extract concepts/i });
  await expect(extract).toBeVisible();
  await extract.click();
  await expect(page.getByTestId("concept-pill").first()).toBeVisible({
    timeout: 600_000,
  });

  // --- 5. Analyse the focal ↔ ED linkage -----------------------------------
  await page
    .getByRole("button", { name: /^edge references .*open-finance/i })
    .first()
    .click();
  const analyze = page.getByRole("button", { name: /analyz/i });
  await expect(analyze).toBeVisible();
  await analyze.click();

  // Findings render as review cards, each quoting its passages verbatim.
  await expect(
    page.getByRole("button", { name: /^Review$/ }).first(),
  ).toBeVisible({ timeout: 600_000 });
});
