import { http, HttpResponse } from "msw";
import type {
  Connection,
  EdgeDetail,
  GraphEdge,
  GraphNode,
  NodeDetail,
  ReviewClause,
  ReviewCounts,
  ReviewFinding,
  ReviewState,
  TaskResponse,
  WorkstreamGraph,
  WorkstreamSummary,
} from "@/lib/types";

// Mirrors data/workstreams/opres-v2/graph.json + findings/*.json exactly.

const TASK_V0_3: TaskResponse = {
  task: {
    id: "opres-pd-v0-3",
    title: "Operational Resilience PD — v0.3",
    source_name: "OpRes PD v0.3 working draft",
    format: ".docx",
    description:
      "Working draft of the Policy Document following the 2025 Discussion Paper",
    status: "in_progress",
    owner: { id: "ar", name: "Aisyah R." },
    reviewers: [
      { id: "fm", name: "Farid M." },
      { id: "ps", name: "Priya S." },
    ],
    clause_count: 42,
    last_edited_at: "2026-07-13T14:30:00Z",
  },
  neighbours: [
    {
      node_id: "bcbs-opres-2021",
      title: "BCBS OpRes 2021",
      node_type: "international-standard",
      edge_type: "contributes-to",
      edge_id: "e-opres_v0_3--bcbs_opres_2021",
      analysed: true,
      findings_count: 3,
    },
    {
      node_id: "fsb-3rd-party",
      title: "FSB 3rd-Party Toolkit",
      node_type: "international-standard",
      edge_type: "contributes-to",
      edge_id: "e-opres_v0_3--fsb_3rd_party",
      analysed: false,
      findings_count: 0,
    },
    {
      node_id: "hkma-spm-or2",
      title: "HKMA SPM OR-2",
      node_type: "peer-regulator",
      edge_type: "contributes-to",
      edge_id: "e-opres_v0_3--hkma_spm_or2",
      analysed: true,
      findings_count: 1,
    },
    {
      node_id: "rmit-pd-2025",
      title: "RMiT PD (28 Nov 2025)",
      node_type: "internal-published",
      edge_type: "parallel-to",
      edge_id: "e-opres_v0_3--rmit_pd_2025",
      analysed: true,
      findings_count: 1,
    },
    {
      node_id: "fsa-2013-143",
      title: "FSA 2013 §143",
      node_type: "act-law",
      edge_type: "references",
      edge_id: "e-opres_v0_3--fsa_2013_143",
      analysed: true,
      findings_count: 1,
    },
    {
      node_id: "abm-position",
      title: "ABM position paper",
      node_type: "industry-input",
      edge_type: "contributes-to",
      edge_id: "e-opres_v0_3--abm_position",
      analysed: false,
      findings_count: 0,
    },
  ],
  draft_empty: false,
};

const TASK_V0_0: TaskResponse = {
  task: {
    id: "opres-pd-v0-0",
    title: "Operational Resilience PD — v0.0",
    source_name: "OpRes PD v0.0 working draft",
    format: ".docx",
    description: "Empty working draft (no clauses parsed yet)",
    status: "in_progress",
    owner: { id: "ar", name: "Aisyah R." },
    reviewers: [
      { id: "fm", name: "Farid M." },
      { id: "ps", name: "Priya S." },
    ],
    clause_count: 0,
    last_edited_at: "2026-07-10T09:00:00Z",
  },
  neighbours: [
    {
      node_id: "bcbs-opres-2021",
      title: "BCBS OpRes 2021",
      node_type: "international-standard",
      edge_type: "contributes-to",
      edge_id: "e-opres_v0_0--bcbs_opres_2021",
      analysed: false,
      findings_count: 0,
    },
    {
      node_id: "hkma-spm-or2",
      title: "HKMA SPM OR-2",
      node_type: "peer-regulator",
      edge_type: "contributes-to",
      edge_id: "e-opres_v0_0--hkma_spm_or2",
      analysed: false,
      findings_count: 0,
    },
  ],
  draft_empty: true,
};

const TASKS: Record<string, TaskResponse> = {
  "opres-pd-v0-3": TASK_V0_3,
  "opres-pd-v0-0": TASK_V0_0,
};

// Non-task nodes present in graph.json (used to assert NOT_A_TASK).
const NODE_TYPES: Record<string, string> = {
  "bcbs-opres-2021": "international-standard",
  "fsb-3rd-party": "international-standard",
  "hkma-spm-or2": "peer-regulator",
  "rmit-pd-2025": "internal-published",
  "fsa-2013-143": "act-law",
  "abm-position": "industry-input",
};

const FINDINGS: Record<string, Connection[]> = {
  "e-opres_v0_3--bcbs_opres_2021": [
    {
      summary: "Dependency mapping tracks BCBS Principle 7",
      label: "aligns-with",
      sentiment: null,
      scope_note: null,
      supported: true,
      source_clauses: [
        {
          clause_number: "Operational Resilience 4.4",
          text: "A financial institution shall map its dependencies on external service providers that support critical operations.",
        },
      ],
      target_clauses: [
        {
          clause_number: "BCBS OpRes Principle 7",
          text: "Banks should manage their dependencies on relationships, including but not limited to those of third parties or intra-group entities.",
        },
      ],
    },
    {
      summary:
        "Board accountability for operational resilience aligns with BCBS Principle 1",
      label: "aligns-with",
      sentiment: null,
      scope_note: null,
      supported: true,
      source_clauses: [
        {
          clause_number: "Operational Resilience 2.1",
          text: "The board shall approve and oversee the financial institution's operational resilience framework, including its risk appetite for disruption to critical operations.",
        },
      ],
      target_clauses: [
        {
          clause_number: "BCBS OpRes Principle 1",
          text: "Banks should utilise their existing governance structure to establish, oversee and implement an effective operational resilience approach.",
        },
      ],
    },
    {
      summary:
        "Draft mandates tested exit plans for critical third parties, going beyond the BCBS baseline",
      label: "goes-beyond",
      sentiment: null,
      scope_note:
        "BCBS Principle 7 expects dependency management but stops short of requiring a tested exit plan per provider.",
      supported: true,
      source_clauses: [
        {
          clause_number: "Operational Resilience 4.7",
          text: "A financial institution shall maintain a documented and periodically tested exit plan for each critical third-party service provider.",
        },
      ],
      target_clauses: [
        {
          clause_number: "BCBS OpRes Principle 7",
          text: "Banks should manage their dependencies on relationships, including but not limited to those of third parties or intra-group entities.",
        },
      ],
    },
  ],
  "e-opres_v0_3--hkma_spm_or2": [
    {
      summary:
        "Annual vs biennial scenario testing — draft pins annual cadence; HKMA requires at least biennial",
      label: "differs-on",
      sentiment: "tighten",
      scope_note: null,
      supported: true,
      source_clauses: [
        {
          clause_number: "Operational Resilience 5.3",
          text: "A financial institution shall conduct scenario testing of its operational resilience arrangements at least annually.",
        },
      ],
      target_clauses: [
        {
          clause_number: "HKMA SPM OR-2 5.2",
          text: "An authorized institution should conduct scenario testing at least once every two years.",
        },
      ],
    },
  ],
  "e-opres_v0_3--rmit_pd_2025": [
    {
      summary:
        "Anchor to superseded RMiT version — draft anchors to the 1 June 2023 RMiT while the 28 Nov 2025 version supersedes it",
      label: "conflicts-with",
      sentiment: null,
      scope_note: null,
      supported: true,
      source_clauses: [
        {
          clause_number: "Operational Resilience 7.1",
          text: "This Policy Document shall be read together with the Risk Management in Technology (RMiT) policy document issued on 1 June 2023.",
        },
      ],
      target_clauses: [
        {
          clause_number: "RMiT PD 1.2",
          text: "This policy document supersedes the Risk Management in Technology policy document issued on 1 June 2023.",
        },
      ],
    },
  ],
  "e-opres_v0_3--fsa_2013_143": [
    {
      summary:
        "Statutory basis correctly cited — preamble anchors this PD to FSA §143(2)",
      label: "aligns-with",
      sentiment: null,
      scope_note: null,
      supported: true,
      source_clauses: [
        {
          clause_number: "Operational Resilience 1.1",
          text: "This policy document is issued pursuant to section 143(2) of the Financial Services Act 2013.",
        },
      ],
      target_clauses: [
        {
          clause_number: "FSA 2013 §143(2)",
          text: "The Bank may issue standards on prudential matters to a financial institution.",
        },
      ],
    },
  ],
  // Canned finding surfaced when Aisyah clicks "Analyze linkages" on FSB.
  "e-opres_v0_3--fsb_3rd_party": [
    {
      summary:
        "Third-party register aligns with FSB Toolkit register expectations",
      label: "aligns-with",
      sentiment: null,
      scope_note: null,
      supported: true,
      source_clauses: [
        {
          clause_number: "Operational Resilience 4.5",
          text: "A financial institution shall maintain a register of arrangements with third-party service providers that support critical operations.",
        },
      ],
      target_clauses: [
        {
          clause_number: "FSB Toolkit Tool 2",
          text: "Financial institutions maintain a comprehensive register of third-party service relationships.",
        },
      ],
    },
  ],
  "e-opres_v0_3--abm_position": [],
};

// --- Graph Screen fixtures (mirror data/workstreams/opres-v2) ---------------

const WORKSTREAMS: WorkstreamSummary[] = [
  {
    id: "opres-v2",
    name: "Operational Resilience v0.3",
    deliverable_type: "Policy Document",
    role: "own",
  },
  {
    id: "outsourcing-v2",
    name: "Outsourcing v2",
    deliverable_type: "Policy Document",
    role: "review",
  },
  {
    id: "rmit-v2-2025",
    name: "RMiT v2 (delivered 28 Nov 2025)",
    deliverable_type: "Policy Document",
    role: "delivered",
  },
];

interface GraphNodeFull extends GraphNode {
  description: string | null;
  source_url: string | null;
}

const GRAPH_NODES: Record<string, GraphNodeFull> = {
  "opres-pd-v0-3": {
    id: "opres-pd-v0-3",
    node_type: "task",
    title: "Operational Resilience PD — v0.3",
    issuer: "BNM",
    short_type: "PD (draft)",
    description: "Working draft of the OpRes Policy Document.",
    source_url: null,
  },
  "bcbs-opres-2021": {
    id: "bcbs-opres-2021",
    node_type: "international-standard",
    title: "BCBS OpRes 2021",
    issuer: "BCBS",
    short_type: "Principles",
    description:
      "Basel Committee Principles for Operational Resilience (2021).",
    source_url: "https://www.bis.org/bcbs/publ/d509.htm",
  },
  "fsb-3rd-party": {
    id: "fsb-3rd-party",
    node_type: "international-standard",
    title: "FSB 3rd-Party Toolkit",
    issuer: "FSB",
    short_type: "Toolkit",
    description: "FSB third-party risk management toolkit (2023).",
    source_url: "https://www.fsb.org",
  },
  "hkma-spm-or2": {
    id: "hkma-spm-or2",
    node_type: "peer-regulator",
    title: "HKMA SPM OR-2",
    issuer: "HKMA",
    short_type: "SPM",
    description: "HKMA Supervisory Policy Manual OR-2.",
    source_url: "https://www.hkma.gov.hk",
  },
  "rmit-pd-2025": {
    id: "rmit-pd-2025",
    node_type: "internal-published",
    title: "RMiT PD (28 Nov 2025)",
    issuer: "BNM",
    short_type: "PD (in force)",
    description: "BNM RMiT policy document, reissued 28 Nov 2025.",
    source_url: "https://www.bnm.gov.my",
  },
  "fsa-2013-143": {
    id: "fsa-2013-143",
    node_type: "act-law",
    title: "FSA 2013 §143",
    issuer: "Parliament",
    short_type: "Act",
    description: "Financial Services Act 2013, section 143.",
    source_url: "https://www.bnm.gov.my",
  },
  "abm-position": {
    id: "abm-position",
    node_type: "industry-input",
    title: "ABM position paper",
    issuer: "ABM",
    short_type: "Position paper",
    description: "ABM position paper on operational resilience.",
    source_url: null,
  },
};

const GRAPH_EDGES: GraphEdge[] = [
  {
    id: "e-opres_v0_3--bcbs_opres_2021",
    source: "opres-pd-v0-3",
    target: "bcbs-opres-2021",
    edge_type: "contributes-to",
    analysed: true,
    findings_count: 3,
  },
  {
    id: "e-opres_v0_3--fsb_3rd_party",
    source: "opres-pd-v0-3",
    target: "fsb-3rd-party",
    edge_type: "contributes-to",
    analysed: false,
    findings_count: 0,
  },
  {
    id: "e-opres_v0_3--hkma_spm_or2",
    source: "opres-pd-v0-3",
    target: "hkma-spm-or2",
    edge_type: "contributes-to",
    analysed: true,
    findings_count: 1,
  },
  {
    id: "e-opres_v0_3--rmit_pd_2025",
    source: "opres-pd-v0-3",
    target: "rmit-pd-2025",
    edge_type: "parallel-to",
    analysed: true,
    findings_count: 1,
  },
  {
    id: "e-opres_v0_3--fsa_2013_143",
    source: "opres-pd-v0-3",
    target: "fsa-2013-143",
    edge_type: "references",
    analysed: true,
    findings_count: 1,
  },
  {
    id: "e-opres_v0_3--abm_position",
    source: "opres-pd-v0-3",
    target: "abm-position",
    edge_type: "contributes-to",
    analysed: false,
    findings_count: 0,
  },
];

const GRAPH_OPRES: WorkstreamGraph = {
  workstream_id: "opres-v2",
  primary_task_id: "opres-pd-v0-3",
  nodes: Object.values(GRAPH_NODES).map(
    ({ id, node_type, title, issuer, short_type }) => ({
      id,
      node_type,
      title,
      issuer,
      short_type,
    }),
  ),
  edges: GRAPH_EDGES,
};

// Canned "Analyze linkages" result for the FSB demo pair (mirrors the backend
// engine.workstreams._DEMO_ANALYZE_FINDINGS — verbatim clause quotes only).
const ANALYZE_FSB: Connection[] = [
  {
    summary:
      "Third-party register aligns with FSB Toolkit register expectations",
    label: "aligns-with",
    sentiment: null,
    scope_note: null,
    supported: true,
    source_clauses: [
      {
        clause_number: "Operational Resilience 4.5",
        text: "A financial institution shall maintain a register of arrangements with third-party service providers that support critical operations.",
      },
    ],
    target_clauses: [
      {
        clause_number: "FSB Toolkit Tool 2",
        text: "Financial institutions maintain a comprehensive register of third-party service relationships.",
      },
    ],
  },
  {
    summary:
      "Draft mandates tested exit plans per critical provider, going beyond the FSB baseline",
    label: "goes-beyond",
    sentiment: null,
    scope_note:
      "The FSB Toolkit expects dependency oversight but stops short of a tested per-provider exit plan.",
    supported: true,
    source_clauses: [
      {
        clause_number: "Operational Resilience 4.7",
        text: "A financial institution shall maintain a documented and periodically tested exit plan for each critical third-party service provider.",
      },
    ],
    target_clauses: [
      {
        clause_number: "FSB Toolkit Tool 6",
        text: "Financial institutions consider exit strategies for critical third-party service relationships.",
      },
    ],
  },
  {
    summary:
      "FSB covers third-party concentration risk; the draft is silent on concentration",
    label: "silent-on",
    sentiment: null,
    scope_note: null,
    supported: true,
    source_clauses: [],
    target_clauses: [
      {
        clause_number: "FSB Toolkit Tool 7",
        text: "Financial authorities monitor systemic third-party dependencies and concentration across the sector.",
      },
    ],
  },
];

const TASK_ACTIVITY = [
  {
    kind: "edit",
    author: "Aisyah R.",
    at: "2026-07-13T14:30:00Z",
    summary: "Revised §5.3 scenario testing cadence",
  },
  {
    kind: "comment",
    author: "Farid M.",
    at: "2026-07-12T16:42:00Z",
    summary: "Suggested tightening §6.3 accountable officer language",
  },
];

function buildNodeDetail(nodeId: string): NodeDetail | null {
  const node = GRAPH_NODES[nodeId];
  if (!node) return null;
  const neighbourIds: string[] = [];
  for (const edge of GRAPH_EDGES) {
    const other =
      edge.source === nodeId
        ? edge.target
        : edge.target === nodeId
          ? edge.source
          : null;
    if (other && !neighbourIds.includes(other)) neighbourIds.push(other);
  }
  return {
    id: node.id,
    node_type: node.node_type,
    title: node.title,
    issuer: node.issuer,
    short_type: node.short_type,
    description: node.description,
    source_url: node.source_url,
    first_order_neighbours: neighbourIds.map((id) => ({
      id,
      node_type: GRAPH_NODES[id].node_type,
      title: GRAPH_NODES[id].title,
    })),
    second_order_neighbours: { status: "placeholder", message: "N/A in demo" },
    recent_activity: node.node_type === "task" ? TASK_ACTIVITY : [],
    concepts: {
      status: "placeholder",
      message: "Concept extraction not enabled in MVP1",
    },
  };
}

function buildEdgeDetail(edgeId: string): EdgeDetail | null {
  const edge = GRAPH_EDGES.find((e) => e.id === edgeId);
  if (!edge) return null;
  const src = GRAPH_NODES[edge.source];
  const tgt = GRAPH_NODES[edge.target];
  return {
    id: edge.id,
    source: { id: src.id, title: src.title, node_type: src.node_type },
    target: { id: tgt.id, title: tgt.title, node_type: tgt.node_type },
    edge_type: edge.edge_type,
    status: edge.analysed ? "analysed" : "not_analysed",
    findings: edge.analysed ? (FINDINGS[edgeId] ?? []) : [],
  };
}

function jsonError(status: number, code: string, message: string) {
  return HttpResponse.json({ code, message }, { status });
}

// --- Review Linkages -------------------------------------------------------
// Mirrors the engine: findings get a derived `~{index}` id and a review_state
// defaulting to "pending"; clause panes are the findings' own cited clauses,
// de-duplicated by number. `reviewState` is per-run mutable so PATCH round-trips
// behave like the real file-backed store; `resetReviewState()` clears it.

const reviewState = new Map<string, ReviewState>();

export function resetReviewState() {
  reviewState.clear();
}

function reviewFindings(edgeId: string): ReviewFinding[] {
  return (FINDINGS[edgeId] ?? []).map((finding, i) => {
    const id = `${edgeId}~${i}`;
    return { ...finding, id, review_state: reviewState.get(id) ?? "pending" };
  });
}

function clausePane(
  findings: ReviewFinding[],
  side: "source" | "target",
): ReviewClause[] {
  const seen = new Set<string>();
  const pane: ReviewClause[] = [];
  for (const finding of findings) {
    for (const clause of finding[`${side}_clauses`]) {
      if (seen.has(clause.clause_number)) continue;
      seen.add(clause.clause_number);
      pane.push({ clause_number: clause.clause_number, text: clause.text });
    }
  }
  return pane;
}

function reviewCounts(findings: ReviewFinding[]): ReviewCounts {
  return {
    total: findings.length,
    accepted: findings.filter((f) => f.review_state === "accepted").length,
    dismissed: findings.filter((f) => f.review_state === "dismissed").length,
  };
}

export const handlers = [
  http.get(
    "*/api/workstreams/:workstreamId/edges/:edgeId/review",
    ({ params }) => {
      const { workstreamId, edgeId } = params as {
        workstreamId: string;
        edgeId: string;
      };
      if (workstreamId !== "opres-v2") {
        return jsonError(
          404,
          "WORKSTREAM_NOT_FOUND",
          `Workstream ${workstreamId} not found`,
        );
      }
      const edge = GRAPH_EDGES.find((e) => e.id === edgeId);
      if (!edge) {
        return jsonError(404, "EDGE_NOT_FOUND", `Edge ${edgeId} not found`);
      }
      // `analysed` is the mock's stand-in for findings-file presence, which is
      // what the engine derives it from. Not FINDINGS membership: FINDINGS also
      // holds what `analyze` *would* return for an as-yet unanalysed edge (the
      // fsb-3rd-party demo pair), which has no file on disk.
      if (!edge.analysed) {
        return jsonError(
          400,
          "EDGE_NOT_ANALYSED",
          `Edge ${edgeId} has not been analysed yet`,
        );
      }
      const findings = reviewFindings(edgeId);
      const node = (id: string) => {
        const n = GRAPH_NODES[id];
        return {
          id,
          title: n?.title ?? null,
          node_type: n?.node_type ?? null,
        };
      };
      return HttpResponse.json({
        edge: {
          id: edgeId,
          edge_type: edge.edge_type,
          source_node: node(edge.source),
          target_node: node(edge.target),
        },
        source_clauses: clausePane(findings, "source"),
        target_clauses: clausePane(findings, "target"),
        findings,
        counts: reviewCounts(findings),
      });
    },
  ),

  http.patch(
    "*/api/workstreams/:workstreamId/edges/:edgeId/findings/:findingId",
    async ({ params, request }) => {
      const { edgeId, findingId } = params as {
        edgeId: string;
        findingId: string;
      };
      const body = (await request.json()) as { review_state?: string };
      const next = body.review_state;
      if (next !== "pending" && next !== "accepted" && next !== "dismissed") {
        return jsonError(
          400,
          "INVALID_REVIEW_STATE",
          `review_state must be pending|accepted|dismissed, got ${next}`,
        );
      }
      const decoded = decodeURIComponent(findingId);
      if (!reviewFindings(edgeId).some((f) => f.id === decoded)) {
        return jsonError(
          404,
          "FINDING_NOT_FOUND",
          `Finding ${decoded} not found on ${edgeId}`,
        );
      }
      reviewState.set(decoded, next);
      const findings = reviewFindings(edgeId);
      return HttpResponse.json({
        finding: findings.find((f) => f.id === decoded),
        counts: reviewCounts(findings),
      });
    },
  ),

  http.get("*/api/workstreams/:workstreamId/tasks/:nodeId", ({ params }) => {
    const { workstreamId, nodeId } = params as {
      workstreamId: string;
      nodeId: string;
    };
    if (workstreamId !== "opres-v2") {
      return jsonError(
        404,
        "WORKSTREAM_NOT_FOUND",
        `Workstream ${workstreamId} not found`,
      );
    }
    const task = TASKS[nodeId];
    if (task) {
      return HttpResponse.json(task);
    }
    if (nodeId in NODE_TYPES) {
      return jsonError(
        400,
        "NOT_A_TASK",
        `Node ${nodeId} is of type ${NODE_TYPES[nodeId]}, not task`,
      );
    }
    return jsonError(
      404,
      "NODE_NOT_FOUND",
      `Node ${nodeId} not found in workstream ${workstreamId}`,
    );
  }),
  http.get(
    "*/api/workstreams/:workstreamId/edges/:edgeId/findings",
    ({ params }) => {
      const { workstreamId, edgeId } = params as {
        workstreamId: string;
        edgeId: string;
      };
      if (workstreamId !== "opres-v2") {
        return jsonError(
          404,
          "WORKSTREAM_NOT_FOUND",
          `Workstream ${workstreamId} not found`,
        );
      }
      return HttpResponse.json(FINDINGS[edgeId] ?? []);
    },
  ),

  // --- Graph Screen routes -------------------------------------------------
  http.get("*/api/workstreams", () => {
    return HttpResponse.json({ workstreams: WORKSTREAMS });
  }),
  http.get("*/api/workstreams/:workstreamId/graph", ({ params }) => {
    const { workstreamId } = params as { workstreamId: string };
    if (workstreamId === "opres-v2") return HttpResponse.json(GRAPH_OPRES);
    // Other seeded workstreams render an empty canvas in component tests.
    return HttpResponse.json({
      workstream_id: workstreamId,
      primary_task_id: null,
      nodes: [],
      edges: [],
    });
  }),
  http.get("*/api/workstreams/:workstreamId/nodes/:nodeId", ({ params }) => {
    const { nodeId } = params as { nodeId: string };
    const detail = buildNodeDetail(nodeId);
    if (!detail) {
      return jsonError(404, "NODE_NOT_FOUND", `Node ${nodeId} not found`);
    }
    return HttpResponse.json(detail);
  }),
  http.get("*/api/workstreams/:workstreamId/edges/:edgeId", ({ params }) => {
    const { edgeId } = params as { edgeId: string };
    const detail = buildEdgeDetail(edgeId);
    if (!detail) {
      return jsonError(404, "EDGE_NOT_FOUND", `Edge ${edgeId} not found`);
    }
    return HttpResponse.json(detail);
  }),
  http.post("*/api/workstreams/:workstreamId/nodes", async ({ request }) => {
    const body = (await request.json()) as {
      node_type: string;
      title: string;
      edges: Array<{ target_node_id: string; edge_type: string }>;
    };
    const id = (body.title || "node")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    return HttpResponse.json(
      {
        id,
        node_type: body.node_type,
        title: body.title,
        created_edges: body.edges.map((e) => {
          // Mirror the backend: a task target stays the edge source.
          const targetIsTask =
            GRAPH_NODES[e.target_node_id]?.node_type === "task";
          const source = targetIsTask ? e.target_node_id : id;
          const target = targetIsTask ? id : e.target_node_id;
          return {
            id: `e-${source}--${target}`,
            source,
            target,
            edge_type: e.edge_type,
            analysed: false,
          };
        }),
      },
      { status: 201 },
    );
  }),
  http.post(
    "*/api/workstreams/:workstreamId/edges/:edgeId/analyze",
    ({ params }) => {
      const { edgeId } = params as { edgeId: string };
      return HttpResponse.json({
        id: edgeId,
        status: "analysed",
        findings: ANALYZE_FSB,
        findings_count: ANALYZE_FSB.length,
      });
    },
  ),
];

export { TASK_V0_3, TASK_V0_0, FINDINGS, GRAPH_OPRES, WORKSTREAMS };
