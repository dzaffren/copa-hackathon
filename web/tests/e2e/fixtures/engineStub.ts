// Deterministic, offline engine stub for the Rulebook Radar E2E suite (#7).
//
// The workspace is a pure read client of the FastAPI engine (engine/api.py):
// `GET /graph`, `GET /nodes/{id}`, `GET /clauses/{clause_number}?version=`. This
// helper intercepts those three routes with `page.route(...)` and fulfils them
// from a small, inline snapshot of the REAL technology-risk corpus
// (`data/artifacts/graph.json` + the clause index) — so every sibling story
// (#26 / #8 / #9 / #10) that mounts the app gets identical, network-free data.
//
// Why route interception (not a running engine): the E2E gate installs browsers
// but no Python engine, and specs must be byte-for-byte deterministic. The glob
// patterns are origin-agnostic, so they intercept the app's calls regardless of
// whatever `VITE_ENGINE_BASE_URL` the dev server was started with; `playwright
// .config.ts` still points it at `ENGINE_STUB_BASE_URL` (a reserved `.test`
// host that never resolves) so any *un-stubbed* engine call fails loudly instead
// of silently reaching a real service.
//
// Contract fidelity: the response shapes bind exactly to `engine/api.py` and the
// Task 2 types (`web/src/types.ts`). `Outsourcing 12.1` is served in the exact
// shape documented in spec-drafter-workspace.md → "API Design / GET /clauses"
// (the clause the core-connection scenario quotes verbatim); an unknown clause
// number yields `404 CLAUSE_NOT_FOUND` and an unknown node id `404
// NODE_NOT_FOUND`, so the verbatim-citation guardrail specs can exercise both.

import type { Page, Route } from "@playwright/test";
import type { Clause, Graph, NodeDetail } from "../../../src/types";

/**
 * The engine origin the E2E app is configured to call. Injected into the Vite
 * dev server's env by `playwright.config.ts`. It is never actually reached — the
 * routes below intercept every request — and `.test` is a reserved TLD that
 * never resolves, so a missing stub surfaces as a hard failure, not flakiness.
 */
export const ENGINE_STUB_BASE_URL = "http://engine.stub.test";

// CORS headers on every fulfilled response: the app (http://localhost:5173)
// fetches a different origin, so the browser needs `Access-Control-Allow-Origin`
// to expose the (faked) response to JS. These are simple GETs — no preflight —
// but the OPTIONS guard below is kept as cheap insurance for reuse by #8's POST.
const CORS_HEADERS: Record<string, string> = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET,POST,OPTIONS",
  "access-control-allow-headers": "*",
};

// ---------------------------------------------------------------------------
// Inline real-corpus snapshot (mirrors data/artifacts/graph.json exactly:
// 7 technology-risk policy nodes + 7 curated/structural edges).
// ---------------------------------------------------------------------------

export const CORPUS_GRAPH: Graph = {
  nodes: [
    {
      id: "rmit-v1-2020",
      policy_id: "rmit",
      title: "Risk Management in Technology (RMiT)",
      version: "v1 · 2020",
      status: "Superseded",
      cluster: "technology-risk",
    },
    {
      id: "rmit-v2-2026-draft",
      policy_id: "rmit",
      title: "Risk Management in Technology (RMiT)",
      version: "v2 · 2026 draft",
      status: "In progress",
      cluster: "technology-risk",
    },
    {
      id: "outsourcing-v1-2019",
      policy_id: "outsourcing",
      title: "Outsourcing",
      version: "v1 · 2019",
      status: "In force",
      cluster: "technology-risk",
    },
    {
      id: "bcm-v1-2022",
      policy_id: "bcm",
      title: "Business Continuity Management",
      version: "v1 · 2022",
      status: "In force",
      cluster: "technology-risk",
    },
    {
      id: "opres-v1-2025-draft",
      policy_id: "opres",
      title: "Operational Resilience",
      version: "draft · Discussion Paper 2025",
      status: "In progress",
      cluster: "technology-risk",
    },
    {
      id: "recovery-planning-v1-2021",
      policy_id: "recovery-planning",
      title: "Recovery Planning",
      version: "v1 · 2021",
      status: "In force",
      cluster: "technology-risk",
    },
    {
      id: "customer-info-v1-2025",
      policy_id: "customer-info",
      title: "Management of Customer Information",
      version: "v1 · 2025",
      status: "In force",
      cluster: "technology-risk",
    },
  ],
  edges: [
    {
      source: "opres-v1-2025-draft",
      target: "bcm-v1-2022",
      type: "overlaps",
      reason:
        "Operational resilience and business continuity overlap on the continuity of critical/essential services after disruption. Operational Resilience 1.1 (continuity of critical financial services) overlaps BCM 9.17 (identified essential services and their supporting systems).",
      source_clauses: ["Operational Resilience 1.1"],
      target_clauses: ["BCM 9.17"],
      provenance: "curated",
      confidence: 1.0,
    },
    {
      source: "outsourcing-v1-2019",
      target: "customer-info-v1-2025",
      type: "overlaps",
      reason:
        "Outsourcing (incl. cloud) that involves a service provider handling customer data engages the Management of Customer Information rules. Outsourcing 12.1 (approval for material outsourcing) engages Customer Info 10.35 (engaging an outsourced service provider that handles customer information).",
      source_clauses: ["Outsourcing 12.1"],
      target_clauses: ["Customer Info 10.35"],
      provenance: "curated",
      confidence: 1.0,
    },
    {
      source: "rmit-v1-2020",
      target: "rmit-v2-2026-draft",
      type: "version-lineage",
      reason:
        "rmit-v1-2020 is superseded by rmit-v2-2026-draft of the same policy.",
      source_clauses: [],
      target_clauses: [],
      provenance: "structural",
      confidence: 1.0,
    },
    {
      source: "rmit-v2-2026-draft",
      target: "bcm-v1-2022",
      type: "overlaps",
      reason:
        "Cloud services supporting critical operations must have continuity arrangements. RMiT 17.1 (cloud adoption for critical systems) engages BCM 9.17 (documenting essential services and the systems that support them).",
      source_clauses: ["RMiT 17.1"],
      target_clauses: ["BCM 9.17"],
      provenance: "curated",
      confidence: 1.0,
    },
    {
      source: "rmit-v2-2026-draft",
      target: "customer-info-v1-2025",
      type: "overlaps",
      reason:
        "Cloud adoption for critical systems often processes customer data offshore. RMiT 17.1 (cloud adoption) engages Customer Info 13.3 (control measures over the disclosure of customer information).",
      source_clauses: ["RMiT 17.1"],
      target_clauses: ["Customer Info 13.3"],
      provenance: "curated",
      confidence: 1.0,
    },
    {
      source: "rmit-v2-2026-draft",
      target: "opres-v1-2025-draft",
      type: "overlaps",
      reason:
        "Both govern the continuity of critical services that depend on cloud/third parties. RMiT 10.50 (cloud risk assessment) overlaps Operational Resilience 1.1 (continuity of critical financial services amid deeper third-party dependencies) — a change in one can duplicate or contradict the other.",
      source_clauses: ["RMiT 10.50"],
      target_clauses: ["Operational Resilience 1.1"],
      provenance: "curated",
      confidence: 1.0,
    },
    {
      source: "rmit-v2-2026-draft",
      target: "outsourcing-v1-2019",
      type: "overlaps",
      reason:
        "A public-cloud arrangement is often also a material outsourcing. RMiT clause 17 (cloud consultation/notification) interacts with Outsourcing 12.1 (written approval) — the core conflict in this cluster.",
      source_clauses: ["RMiT 17.1", "RMiT 17.2"],
      target_clauses: ["Outsourcing 12.1"],
      provenance: "curated",
      confidence: 1.0,
    },
  ],
};

// Verbatim clause bodies for every clause anchored by an edge above. `text` is
// the real clause text from the parsed corpus, EXCEPT `Outsourcing 12.1`, which
// is served in the exact composed shape documented in the spec's API Design (the
// sentence the core-connection scenario quotes: clause 12.1 + sub-item (a)).
export const CORPUS_CLAUSES: Record<string, Clause> = {
  "Outsourcing 12.1": {
    clause_number: "Outsourcing 12.1",
    text: "A financial institution must obtain the Bank's written approval before entering into a new material outsourcing arrangement.",
    policy_id: "outsourcing",
    document_id: "outsourcing-v1-2019",
    source: "published",
    heading: "Application for approval",
    parent: "Outsourcing 12",
    children: [],
    superseded_versions: [],
  },
  "Operational Resilience 1.1": {
    clause_number: "Operational Resilience 1.1",
    text: "This Discussion Paper sets out the emerging direction for strengthening the\ncontinuity of critical financial services in an environment shaped by rapid\ndigitalisation, rising cyber threats, deeper third-party dependencies, and\nincreasing severity and frequency of disruptions.",
    policy_id: "opres",
    document_id: "opres-v1-2025-draft",
    source: "draft",
    heading: null,
    parent: null,
    children: [],
    superseded_versions: [],
  },
  "RMiT 17.1": {
    clause_number: "RMiT 17.1",
    text: "A financial institution shall notify the Bank within 14 days of the first-time adoption of a public cloud service for a critical system, having first:",
    policy_id: "rmit",
    document_id: "rmit-v2-2026-draft",
    source: "draft",
    heading: "17 Cloud services",
    parent: null,
    children: [],
    superseded_versions: [],
  },
  "RMiT 17.2": {
    clause_number: "RMiT 17.2",
    text: "A financial institution shall notify the Bank of any subsequent adoption of a\npublic cloud service for a critical system, by submitting the notification\ntogether with the necessary updates to all the information required under\nparagraph 17.1. Such subsequent notification relies on and draws directly\nfrom the consultation under paragraph 17.1, and the financial institution\nmust confirm that the risk assessment, readiness confirmation and\nindependent pre-implementation review carried out for that prior\nconsultation under paragraph 17.1 remain valid and have been updated, as\nnecessary, to reflect the subsequent adoption.",
    policy_id: "rmit",
    document_id: "rmit-v2-2026-draft",
    source: "draft",
    heading: "17 Cloud services",
    parent: null,
    children: [],
    superseded_versions: [],
  },
  "RMiT 10.50": {
    clause_number: "RMiT 10.50",
    text: "A financial institution must fully understand the inherent risk of adopting\ncloud services. In this regard, a financial institution shall conduct a\ncomprehensive risk assessment prior to cloud adoption which considers the\ninherent architecture of cloud services that leverages on the sharing of\nresources and services across multiple tenants over the Internet.",
    policy_id: "rmit",
    document_id: "rmit-v2-2026-draft",
    source: "draft",
    heading: "10 Technology Operations Management",
    parent: null,
    children: [],
    superseded_versions: [],
  },
  "BCM 9.17": {
    clause_number: "BCM 9.17",
    text: "A financial institution must maintain proper documentation and records of all\nidentified essential services, as well as the business functions, processes and\nsystems that support these essential services, which are to be made available\nto the Bank upon request.",
    policy_id: "bcm",
    document_id: "bcm-v1-2022",
    source: "published",
    heading: null,
    parent: null,
    children: [],
    superseded_versions: [],
  },
  "Customer Info 10.35": {
    clause_number: "Customer Info 10.35",
    text: "FSPs must assess the risks and benefits of engaging an outsourced service\nprovider for the destruction of customer information which involves transporting\ncustomer information outside the FSP's premises.",
    policy_id: "customer-info",
    document_id: "customer-info-v1-2025",
    source: "published",
    heading: null,
    parent: null,
    children: [],
    superseded_versions: [],
  },
  "Customer Info 13.3": {
    clause_number: "Customer Info 13.3",
    text: "Financial institutions are required to put in place adequate control measures\nover the disclosure of customer information to any parties which are permitted\nunder the FSA, IFSA or DFIA, which at a minimum shall include-",
    policy_id: "customer-info",
    document_id: "customer-info-v1-2025",
    source: "published",
    heading: null,
    parent: null,
    children: [],
    superseded_versions: [],
  },
};

/**
 * Options for `installEngineStub`. Every field is optional — the defaults serve
 * the real corpus above. Sibling stories override to inject reference nodes,
 * extra clauses, or bespoke node-detail shapes without a running engine.
 */
export interface EngineStubOptions {
  /** Replace the whole graph served at `GET /graph`. Defaults to `CORPUS_GRAPH`. */
  graph?: Graph;
  /** Extra/overriding clause bodies, merged over `CORPUS_CLAUSES` by number. */
  clauses?: Record<string, Clause>;
  /** Extra/overriding `GET /nodes/{id}` bodies; otherwise derived from `graph`. */
  nodes?: Record<string, NodeDetail>;
}

/**
 * Intercept the engine's three read routes for `page` and fulfil them from the
 * inline corpus (plus any `opts` overrides). Call once at the top of each E2E
 * spec (or in a `beforeEach`) before navigating, so the workspace loads
 * deterministic, offline data.
 */
export async function installEngineStub(
  page: Page,
  opts: EngineStubOptions = {},
): Promise<void> {
  const graph = opts.graph ?? CORPUS_GRAPH;
  const clauses = { ...CORPUS_CLAUSES, ...(opts.clauses ?? {}) };
  const nodeOverrides = opts.nodes ?? {};

  // GET /graph — the whole knowledge graph (single source of truth for the map).
  await page.route("**/graph", async (route) => {
    if (isPreflight(route)) return preflight(route);
    await fulfilJson(route, 200, graph);
  });

  // GET /nodes/{id} — derived node detail (outgoing edges only), mirroring
  // engine/api.py's `get_node`; an unknown id → 404 NODE_NOT_FOUND.
  await page.route("**/nodes/*", async (route) => {
    if (isPreflight(route)) return preflight(route);
    const id = segmentAfter(route.request().url(), "/nodes/");
    const detail = nodeOverrides[id] ?? deriveNodeDetail(graph, id);
    if (!detail) {
      return fulfilError(
        route,
        404,
        "NODE_NOT_FOUND",
        `No node with id '${id}'`,
      );
    }
    await fulfilJson(route, 200, detail);
  });

  // GET /clauses/{clause_number}?version= — verbatim clause text. An unknown
  // clause → 404 CLAUSE_NOT_FOUND (the guardrail path → "No matching clause
  // found"); a known clause with an unknown version → 404 CLAUSE_VERSION_NOT_FOUND.
  await page.route("**/clauses/*", async (route) => {
    if (isPreflight(route)) return preflight(route);
    const url = new URL(route.request().url());
    const clauseNumber = decodeURIComponent(
      url.pathname.slice(
        url.pathname.indexOf("/clauses/") + "/clauses/".length,
      ),
    );
    const version = url.searchParams.get("version");
    const clause = clauses[clauseNumber];
    if (!clause) {
      return fulfilError(
        route,
        404,
        "CLAUSE_NOT_FOUND",
        `No matching clause found for '${clauseNumber}'`,
      );
    }
    if (version && !(clause.superseded_versions ?? []).includes(version)) {
      return fulfilError(
        route,
        404,
        "CLAUSE_VERSION_NOT_FOUND",
        `No version '${version}' for clause '${clauseNumber}'`,
      );
    }
    await fulfilJson(route, 200, clause);
  });
}

// --- helpers ---------------------------------------------------------------

/** Build the `GET /nodes/{id}` shape from the graph, or `null` for an unknown id. */
function deriveNodeDetail(graph: Graph, id: string): NodeDetail | null {
  const node = graph.nodes.find((n) => n.id === id);
  if (!node) return null;
  return {
    id: node.id,
    title: node.title,
    status: node.status,
    edges: graph.edges
      .filter((e) => e.source === id)
      .map((e) => ({ target: e.target, type: e.type, reason: e.reason })),
  };
}

/** Decode the path segment following `marker` in a full request URL. */
function segmentAfter(url: string, marker: string): string {
  const { pathname } = new URL(url);
  return decodeURIComponent(
    pathname.slice(pathname.indexOf(marker) + marker.length),
  );
}

function isPreflight(route: Route): boolean {
  return route.request().method() === "OPTIONS";
}

function preflight(route: Route): Promise<void> {
  return route.fulfill({ status: 204, headers: CORS_HEADERS, body: "" });
}

function fulfilJson(
  route: Route,
  status: number,
  body: unknown,
): Promise<void> {
  return route.fulfill({
    status,
    headers: { ...CORS_HEADERS, "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

/** Emit the engine's uniform error body `{ error, message }` at `status`. */
function fulfilError(
  route: Route,
  status: number,
  code: string,
  message: string,
): Promise<void> {
  return fulfilJson(route, status, { error: code, message });
}
