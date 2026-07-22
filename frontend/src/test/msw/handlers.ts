import { http, HttpResponse } from "msw";
import type {
  Connection,
  CopilotIntent,
  CreateWorkstreamRequest,
  CreateWorkstreamResponse,
  CrossLink,
  DraftResponse,
  EdgeDetail,
  GraphEdge,
  GraphNode,
  LinkageCard,
  NodeDetail,
  Person,
  ReviewClause,
  ReviewCounts,
  ReviewFinding,
  ReviewState,
  TaskResponse,
  TaskWorkflow,
  WorkstreamGraph,
  WorkstreamSummary,
} from "@/lib/types";

// Mirrors data/workstreams/opres-v2/graph.json + findings/*.json exactly.

const DRAFT_WORKFLOW: TaskWorkflow = {
  status: "draft",
  checker: null,
  approved_by: null,
  approved_at: null,
};

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
    {
      node_id: "opres-dp-2025",
      title: "OpRes DP (Dec 2025)",
      node_type: "internal-published",
      edge_type: "references",
      edge_id: "e-opres_v0_3--opres_dp_2025",
      analysed: false,
      findings_count: 0,
    },
  ],
  workflow: DRAFT_WORKFLOW,
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
  workflow: DRAFT_WORKFLOW,
  draft_empty: true,
};

const TASKS: Record<string, TaskResponse> = {
  "opres-pd-v0-3": TASK_V0_3,
  "opres-pd-v0-0": TASK_V0_0,
};

// Mutable per-task workflow overrides, so a PATCH .../workflow round-trips
// like the real file-backed store. Absent entry -> the task's seeded default.
const taskWorkflow = new Map<string, TaskWorkflow>();

export function resetTaskWorkflow() {
  taskWorkflow.clear();
}

// Non-task nodes present in graph.json (used to assert NOT_A_TASK).
const NODE_TYPES: Record<string, string> = {
  "bcbs-opres-2021": "international-standard",
  "fsb-3rd-party": "international-standard",
  "hkma-spm-or2": "peer-regulator",
  "rmit-pd-2025": "internal-published",
  "fsa-2013-143": "act-law",
  "abm-position": "industry-input",
  "opres-dp-2025": "internal-published",
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
          clause_number: "OpRes PD 4.4",
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
          clause_number: "OpRes PD 2.1",
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
          clause_number: "OpRes PD 4.7",
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
          clause_number: "OpRes PD 5.3",
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
          clause_number: "OpRes PD 7.1",
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
          clause_number: "OpRes PD 1.1",
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
          clause_number: "OpRes PD 4.5",
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
  document_id: string | null;
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
    document_id: "opres-v1-2025-draft",
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
    document_id: null,
  },
  "fsb-3rd-party": {
    id: "fsb-3rd-party",
    node_type: "international-standard",
    title: "FSB 3rd-Party Toolkit",
    issuer: "FSB",
    short_type: "Toolkit",
    description: "FSB third-party risk management toolkit (2023).",
    source_url: "https://www.fsb.org",
    document_id: null,
  },
  "hkma-spm-or2": {
    id: "hkma-spm-or2",
    node_type: "peer-regulator",
    title: "HKMA SPM OR-2",
    issuer: "HKMA",
    short_type: "SPM",
    description: "HKMA Supervisory Policy Manual OR-2.",
    source_url: "https://www.hkma.gov.hk",
    document_id: null,
  },
  "rmit-pd-2025": {
    id: "rmit-pd-2025",
    node_type: "internal-published",
    title: "RMiT PD (28 Nov 2025)",
    issuer: "BNM",
    short_type: "PD (in force)",
    description: "BNM RMiT policy document, reissued 28 Nov 2025.",
    source_url: "https://www.bnm.gov.my",
    document_id: "rmit-v2-2025",
  },
  "fsa-2013-143": {
    id: "fsa-2013-143",
    node_type: "act-law",
    title: "FSA 2013 §143",
    issuer: "Parliament",
    short_type: "Act",
    description: "Financial Services Act 2013, section 143.",
    source_url: "https://www.bnm.gov.my",
    document_id: null,
  },
  "abm-position": {
    id: "abm-position",
    node_type: "industry-input",
    title: "ABM position paper",
    issuer: "ABM",
    short_type: "Position paper",
    description: "ABM position paper on operational resilience.",
    source_url: null,
    document_id: null,
  },
  "opres-dp-2025": {
    id: "opres-dp-2025",
    node_type: "internal-published",
    title: "OpRes DP (Dec 2025)",
    issuer: "BNM",
    short_type: "DP",
    description:
      "Operational Resilience Discussion Paper, December 2025 — the consultation the v0.3 PD draft follows.",
    source_url: null,
    document_id: "opres-v1-2025-draft",
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
  {
    id: "e-opres_v0_3--opres_dp_2025",
    source: "opres-pd-v0-3",
    target: "opres-dp-2025",
    edge_type: "references",
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
        clause_number: "OpRes PD 4.5",
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
        clause_number: "OpRes PD 4.7",
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
    ismp_classification: null,
    pursuant_to: null,
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
    source: {
      id: src.id,
      title: src.title,
      node_type: src.node_type,
      document_id: src.document_id,
    },
    target: {
      id: tgt.id,
      title: tgt.title,
      node_type: tgt.node_type,
      document_id: tgt.document_id,
    },
    edge_type: edge.edge_type,
    status: edge.analysed ? "analysed" : "not_analysed",
    findings: edge.analysed ? (FINDINGS[edgeId] ?? []) : [],
    analysable: Boolean(src.document_id && tgt.document_id),
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

// --- Drafting Workspace ----------------------------------------------------
// Mirrors the engine: reviewed-linkages aggregates ACCEPTED findings across the
// task's incident edges (reusing the same reviewState map, so accepting on the
// review screen shows up here exactly as it does against the real store), and
// related-linkages is empty because opres-v2 genuinely has no anchor↔anchor
// edges. The Copilot replies from a script, never a model.

const SEEDED_DRAFT_HTML =
  "<h1>Operational Resilience</h1>\n<p><strong>5.3</strong> A financial institution shall conduct scenario testing of its operational resilience arrangements at least annually.</p>";

let draftHtml = SEEDED_DRAFT_HTML;
let draftSavedAt: string | null = "2026-07-13T14:30:00Z";

export function resetDraft() {
  draftHtml = SEEDED_DRAFT_HTML;
  draftSavedAt = "2026-07-13T14:30:00Z";
}

const NODE_TITLES: Record<string, string> = Object.fromEntries(
  Object.entries(GRAPH_NODES).map(([id, n]) => [id, n.title]),
);

function linkageCard(finding: ReviewFinding, edge: GraphEdge): LinkageCard {
  return {
    id: finding.id,
    label: finding.label,
    sentiment: finding.sentiment,
    summary: finding.summary,
    edge_id: edge.id,
    left: {
      id: edge.source,
      title: NODE_TITLES[edge.source] ?? edge.source,
      node_type: GRAPH_NODES[edge.source]?.node_type ?? null,
    },
    right: {
      id: edge.target,
      title: NODE_TITLES[edge.target] ?? edge.target,
      node_type: GRAPH_NODES[edge.target]?.node_type ?? null,
    },
    source_clause_number: finding.source_clauses[0]?.clause_number ?? null,
    target_clause_number: finding.target_clauses[0]?.clause_number ?? null,
  };
}

// The scripted PD reply, quoting RMiT 9.4 verbatim. Kept in step with
// engine/copilot_scripts.py, whose own test re-resolves the quote against the
// built clause index.
const RMIT_9_4_QUOTE =
  "A financial institution must designate a Chief Information Security (CISO) by whatever name called, to be responsible for the technology risk management function of the financial institution.";

const COPILOT_SCRIPT: Record<string, unknown[]> = {
  PD: [
    {
      role: "copilot",
      text: "Hi Aisyah — I've loaded your accepted linkages and the OpRes DP feedback register. The draft has no §6.3 yet. Want me to draft the accountable-officer preamble that goes beyond RMiT?",
    },
    {
      role: "copilot",
      text: "Here is a neutral §6.3 preamble, grounded in RMiT 9.4.",
      citations: [{ clause_number: "RMiT 9.4", text: RMIT_9_4_QUOTE }],
      snippet_html:
        "<h2>PART E — ACCOUNTABILITY</h2>\n<p><strong>6.3</strong> A financial institution shall designate a single accountable officer for operational resilience.</p>",
    },
  ],
  DP: [{ role: "copilot", text: "Discussion Paper mode." }],
  ED: [{ role: "copilot", text: "Exposure Draft mode." }],
  FAQ: [{ role: "copilot", text: "FAQ mode." }],
  "Engagement Deck": [{ role: "copilot", text: "Engagement deck mode." }],
  "Feedback Template for Industry": [
    { role: "copilot", text: "Feedback template mode." },
  ],
  "Peer Benchmarking": [{ role: "copilot", text: "Peer benchmarking mode." }],
};

// --- New Workstream --------------------------------------------------------
// Mirrors the engine: the reviewer list excludes the owner, create slugs the
// name and appends to the in-memory workstream list so the sidebar picks it up,
// and validation returns {code, message, field}.

const DIRECTORY: Person[] = [
  { id: "fm", name: "Farid M." },
  { id: "ps", name: "Priya S." },
  { id: "jn", name: "Jarod N." },
];

const DELIVERABLE_LABELS: Record<string, string> = {
  PD: "Policy Document",
  ED: "Exposure Draft",
  DP: "Discussion Paper",
  Other: "Other",
};

let createdWorkstreams: WorkstreamSummary[] = [];

export function resetCreatedWorkstreams() {
  createdWorkstreams = [];
}

// Mirrors data/workstreams/_cross/: one link, OpRes DP <-> Open Finance ED,
// projected from the real 2026-07-11 finder+critic trace.
const CROSS_LINK: CrossLink = {
  id: "x-open_finance_ed--opres_dp_2025",
  edge_type: "parallel-to",
  near: {
    node_id: "opres-dp-2025",
    title: "OpRes DP (Dec 2025)",
    workstream_id: "opres-v2",
  },
  far: {
    node_id: "of-ed-2025",
    title: "Open Finance ED — 18 Nov 2025",
    workstream_id: "open-finance-ed",
    workstream_name: "Open Finance ED · 2025",
  },
  findings_count: 12,
  labels: { "aligns-with": 6, "differs-on": 4, "goes-beyond": 2 },
  counts: { total: 12, accepted: 0, dismissed: 0 },
  classification: "divergent",
  risk_level: "medium",
  detected_at: "2026-07-11",
  shared_attributes: {
    legal_basis: ["FSA 2013"],
    applicability: ["licensed banks"],
    keywords: ["operational resilience"],
    policy_owner: null,
    ismp_classification: null,
  },
  reasons: [
    "Both apply to licensed banks",
    "Both issued under FSA 2013",
    "Both address operational resilience",
    "The linkages differ on 4 requirement(s)",
  ],
};

// --- Per-linkage Maker-Checker (Phase 3) -----------------------------------
// A minimal in-memory mirror of engine/linkage_review.py so the Review Queue's
// transitions round-trip within a test. Reset in setup.ts's afterEach.
const PEOPLE_BY_ID: Record<string, Person> = {
  ar: { id: "ar", name: "Aisyah R." },
  fm: { id: "fm", name: "Farid M." },
  ps: { id: "ps", name: "Priya S." },
  jn: { id: "jn", name: "Jarod N." },
};

const QUEUE_SEED = [
  {
    workstream_id: "_cross",
    edge_id: "x-bcm_pd_2022--rrp_pd_v0_1",
    finding_id: "x-bcm_pd_2022--rrp_pd_v0_1~0",
    summary: "Both preserve continuity of critical functions",
    label: "aligns-with" as const,
    sentiment: null,
    near: {
      node_id: "bcm-pd-2022",
      title: "BCM PD (19 Dec 2022)",
      workstream_id: "bcm",
      workstream_name: "Business Continuity Management",
    },
    far: {
      node_id: "rrp-pd-v0-1",
      title: "Recovery Planning PD — v0.1",
      workstream_id: "resolution-recovery",
      workstream_name: "Resolution & Recovery Planning",
    },
  },
  {
    workstream_id: "_cross",
    edge_id: "x-open_finance_ed--opres_dp_2025",
    finding_id: "x-open_finance_ed--opres_dp_2025~0",
    summary: "Open finance board oversight goes beyond the DP",
    label: "goes-beyond" as const,
    sentiment: null,
    near: {
      node_id: "of-ed-2025",
      title: "Open Finance ED",
      workstream_id: "open-finance-ed",
      workstream_name: "Open Finance ED · 2025",
    },
    far: {
      node_id: "opres-dp-2025",
      title: "OpRes DP (Dec 2025)",
      workstream_id: "opres-v2",
      workstream_name: "Operational Resilience v0.3",
    },
  },
];

const MSW_TRANSITIONS: Record<
  string,
  { from: string[]; to: string; role: "maker" | "checker" }
> = {
  claim: { from: ["ai_detected"], to: "maker_review", role: "maker" },
  submit: { from: ["maker_review", "changes_requested"], to: "submitted_for_check", role: "maker" },
  pick_up: { from: ["submitted_for_check"], to: "checker_review", role: "checker" },
  approve: { from: ["checker_review"], to: "approved", role: "checker" },
  reject: { from: ["checker_review"], to: "rejected", role: "checker" },
  request_changes: { from: ["checker_review"], to: "changes_requested", role: "checker" },
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let linkageReviews: Record<string, any> = {};
export function resetLinkageReview() {
  linkageReviews = {};
}
function defaultRecord() {
  return {
    status: "ai_detected",
    maker: null,
    checker: null,
    created_at: null,
    checked_at: null,
    comments: [],
    audit: [],
  };
}
function recordFor(findingId: string) {
  return linkageReviews[findingId] ?? defaultRecord();
}

export const handlers = [
  // Review Queue: cross-workstream linkages with their maker-checker status.
  http.get("*/api/review-queue", () => {
    const items = QUEUE_SEED.map((s) => {
      const r = recordFor(s.finding_id);
      return {
        ...s,
        status: r.status,
        maker: r.maker,
        checker: r.checker,
        created_at: r.created_at,
        checked_at: r.checked_at,
      };
    });
    const counts: Record<string, number> = {
      ai_detected: 0,
      maker_review: 0,
      submitted_for_check: 0,
      checker_review: 0,
      approved: 0,
      rejected: 0,
      changes_requested: 0,
    };
    for (const it of items) counts[it.status] = (counts[it.status] ?? 0) + 1;
    return HttpResponse.json({ items, counts_by_status: counts });
  }),

  http.get(
    "*/api/workstreams/:workstreamId/edges/:edgeId/linkage-review",
    ({ params }) => {
      const edgeId = params.edgeId as string;
      const linkages = QUEUE_SEED.filter((s) => s.edge_id === edgeId).map((s) => ({
        finding_id: s.finding_id,
        summary: s.summary,
        label: s.label,
        sentiment: s.sentiment,
        review: recordFor(s.finding_id),
      }));
      return HttpResponse.json({ edge_id: edgeId, linkages });
    },
  ),

  http.patch(
    "*/api/workstreams/:workstreamId/edges/:edgeId/findings/:findingId/linkage-review",
    async ({ params, request }) => {
      const findingId = params.findingId as string;
      const body = (await request.json()) as {
        action: string;
        actor_id: string;
        comment?: string;
      };
      const transition = MSW_TRANSITIONS[body.action];
      if (!transition) return jsonError(400, "INVALID_ACTION", "Unknown action");
      const actor = PEOPLE_BY_ID[body.actor_id];
      if (!actor) return jsonError(400, "UNKNOWN_ACTOR", "Unknown actor");

      const record = { ...recordFor(findingId) };
      record.comments = [...record.comments];
      record.audit = [...record.audit];
      if (!transition.from.includes(record.status)) {
        return jsonError(
          400,
          "INVALID_WORKFLOW_STATE",
          `Action '${body.action}' not allowed from '${record.status}'`,
        );
      }
      const at = new Date().toISOString();
      if (body.action === "claim") {
        record.maker = actor;
        record.created_at = at;
      } else if (body.action === "pick_up") {
        if (record.maker && record.maker.id === actor.id) {
          return jsonError(400, "SAME_ACTOR", "The checker cannot be the maker");
        }
        record.checker = actor;
      }
      if (transition.to === "approved" || transition.to === "rejected") {
        record.checked_at = at;
      }
      if (body.comment) {
        record.comments.push({ author: actor, at, text: body.comment });
      }
      record.audit.push({
        actor,
        action: body.action,
        from: record.status,
        to: transition.to,
        at,
        comment: body.comment ?? null,
      });
      record.status = transition.to;
      linkageReviews[findingId] = record;
      return HttpResponse.json({ finding_id: findingId, review: record });
    },
  ),

  // The _cross store is served by the ordinary review route. Two of the twelve
  // findings are enough to prove the screen reads them unchanged.
  http.get("*/api/workstreams/_cross/edges/:edgeId/review", ({ params }) => {
    const edgeId = params.edgeId as string;
    const findings = [
      {
        summary:
          "Open finance's requirement for board and senior management oversight goes beyond the discussion paper's responsibility mapping",
        label: "goes-beyond" as const,
        sentiment: null,
        scope_note:
          "Open finance does not mandate a single ultimately-accountable person for operational resilience outcomes.",
        supported: true,
        source_clauses: [
          {
            clause_number: "Open Finance 7.1",
            text: "The board and senior management shall exercise effective oversight of an FSP's implementation of open finance.",
          },
        ],
        target_clauses: [
          {
            clause_number: "Operational Resilience 6.3",
            text: "Responsibility Mapping identifies the person accountable for each critical operation.",
          },
        ],
      },
      {
        summary:
          "Both documents rely on the same underlying policy documents but anchor to different RMiT versions",
        label: "aligns-with" as const,
        sentiment: null,
        scope_note: null,
        supported: true,
        source_clauses: [
          {
            clause_number: "Open Finance 6.1(h)",
            text: "Policy Document on Risk Management in Technology issued on 1 June",
          },
        ],
        target_clauses: [
          {
            clause_number: "Operational Resilience 7.2",
            text: "This Discussion Paper should be read together with the Risk Management in Technology policy document.",
          },
        ],
      },
    ].map((f, i) => ({
      ...f,
      id: `${edgeId}~${i}`,
      review_state: reviewState.get(`${edgeId}~${i}`) ?? "pending",
    }));

    return HttpResponse.json({
      edge: {
        id: edgeId,
        edge_type: "parallel-to",
        source_node: {
          id: "of-ed-2025",
          title: "Open Finance ED — 18 Nov 2025",
          node_type: "task",
        },
        target_node: {
          id: "opres-dp-2025",
          title: "OpRes DP (Dec 2025)",
          node_type: "internal-published",
        },
      },
      source_clauses: findings.flatMap((f) => f.source_clauses),
      target_clauses: findings.flatMap((f) => f.target_clauses),
      findings,
      counts: reviewCounts(findings as never),
    });
  }),

  // Aggregate cross-links (Overlap Alerts card + Cross-Workstream Intelligence
  // metrics/list). Empty by default so the App smoke test's plain "/" render
  // doesn't surface an alert; tests for those surfaces override this handler
  // with `server.use(...)`.
  http.get("*/api/cross-links", () => {
    return HttpResponse.json({ links: [] });
  }),

  // Relationship detail (Cross-Workstream Intelligence panel). Serves the
  // seeded link with both regulatory profiles, shared attributes, reasons and
  // verbatim clause evidence.
  http.get("*/api/cross-links/:edgeId", ({ params }) => {
    const edgeId = params.edgeId as string;
    return HttpResponse.json({
      id: edgeId,
      edge_type: "parallel-to",
      detected_at: CROSS_LINK.detected_at,
      classification: CROSS_LINK.classification,
      risk_level: CROSS_LINK.risk_level,
      near: {
        node_id: "opres-dp-2025",
        title: "OpRes DP (Dec 2025)",
        node_type: "internal-published",
        issuer: "BNM",
        short_type: "DP",
        description: null,
        workstream_id: "opres-v2",
        workstream_name: "Operational Resilience v0.3",
        concepts: {
          status: "available",
          policy_owner: "Aisyah R.",
          applicability: null,
          empowerment_framework: null,
          requirement: null,
          issuance_date: null,
          effective_date: null,
          keywords: ["operational resilience"],
          legal_basis: ["FSA 2013"],
          ismp_classification: null,
        },
      },
      far: {
        node_id: "of-ed-2025",
        title: "Open Finance ED — 18 Nov 2025",
        node_type: "task",
        issuer: "BNM",
        short_type: "ED",
        description: null,
        workstream_id: "open-finance-ed",
        workstream_name: "Open Finance ED · 2025",
        concepts: {
          status: "available",
          policy_owner: "Jarod N.",
          applicability: null,
          empowerment_framework: null,
          requirement: null,
          issuance_date: "2025-11-18",
          effective_date: null,
          keywords: ["open finance", "operational resilience"],
          legal_basis: ["FSA 2013"],
          ismp_classification: null,
        },
      },
      shared_attributes: CROSS_LINK.shared_attributes,
      reasons: CROSS_LINK.reasons,
      labels: CROSS_LINK.labels,
      counts: CROSS_LINK.counts,
      findings: [
        {
          id: `${edgeId}~0`,
          review_state: "pending",
          summary:
            "Open finance's board oversight requirement goes beyond the DP's responsibility mapping",
          label: "goes-beyond",
          sentiment: null,
          scope_note: "No single accountable person is mandated.",
          supported: true,
          source_clauses: [
            {
              clause_number: "Open Finance 7.1",
              text: "The board and senior management shall exercise effective oversight of an FSP's implementation of open finance.",
            },
          ],
          target_clauses: [
            {
              clause_number: "Operational Resilience 6.3",
              text: "Responsibility Mapping identifies the person accountable for each critical operation.",
            },
          ],
        },
      ],
    });
  }),

  http.get("*/api/workstreams/:workstreamId/cross-links", ({ params }) => {
    // Only opres-v2 and open-finance-ed touch the seeded link.
    const id = params.workstreamId as string;
    if (id === "opres-v2") return HttpResponse.json({ links: [CROSS_LINK] });
    if (id === "open-finance-ed") {
      // Read from the other end: near/far swap, and `workstream_name` belongs
      // to whichever side is now far.
      return HttpResponse.json({
        links: [
          {
            ...CROSS_LINK,
            near: { ...CROSS_LINK.far, workstream_name: undefined },
            far: {
              ...CROSS_LINK.near,
              workstream_name: "Operational Resilience v0.3",
            },
          },
        ],
      });
    }
    return HttpResponse.json({ links: [] });
  }),

  http.get("*/api/reviewers", () => {
    return HttpResponse.json({ reviewers: DIRECTORY });
  }),

  http.post("*/api/workstreams", async ({ request }) => {
    const body = (await request.json()) as CreateWorkstreamRequest;
    const name = (body.name ?? "").trim();
    if (!name) {
      return HttpResponse.json(
        {
          code: "NAME_REQUIRED",
          message: "Give the workstream a name.",
          field: "name",
        },
        { status: 400 },
      );
    }
    if (name.length > 120) {
      return HttpResponse.json(
        {
          code: "NAME_TOO_LONG",
          message: "Workstream name must be 120 characters or fewer.",
          field: "name",
        },
        { status: 400 },
      );
    }
    const id = name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
    const created: CreateWorkstreamResponse = {
      id,
      name,
      deliverable_type: DELIVERABLE_LABELS[body.deliverable_type] ?? "Other",
      role: "own",
      description: body.description ?? null,
      primary_task_id: null,
      target_publication: body.target_publication ?? null,
      owner: { id: "ar", name: "Aisyah R." },
      reviewers: (body.reviewer_ids ?? []).map((rid) =>
        DIRECTORY.find((d) => d.id === rid)!,
      ),
      access: body.access,
      created_at: "2026-07-16T09:00:00Z",
    };
    createdWorkstreams.push({
      id,
      name,
      deliverable_type: created.deliverable_type,
      role: "own",
    });
    return HttpResponse.json(created, { status: 201 });
  }),

  http.get(
    "*/api/workstreams/:workstreamId/tasks/:nodeId/reviewed-linkages",
    ({ params }) => {
      const nodeId = params.nodeId as string;
      if (!TASKS[nodeId]) {
        return HttpResponse.json(
          { code: "TASK_NOT_FOUND", message: `${nodeId} is not a task` },
          { status: 404 },
        );
      }
      const cards: LinkageCard[] = [];
      for (const edge of GRAPH_EDGES) {
        if (edge.source !== nodeId && edge.target !== nodeId) continue;
        for (const f of reviewFindings(edge.id)) {
          if (f.review_state === "accepted") cards.push(linkageCard(f, edge));
        }
      }
      return HttpResponse.json({ findings: cards });
    },
  ),

  http.get(
    "*/api/workstreams/:workstreamId/tasks/:nodeId/related-linkages",
    ({ request, params }) => {
      const hops = new URL(request.url).searchParams.get("hops");
      if (hops !== null && hops !== "1") {
        return HttpResponse.json(
          { code: "HOPS_OUT_OF_RANGE", message: "Only hops=1 is supported" },
          { status: 400 },
        );
      }
      if (!TASKS[params.nodeId as string]) {
        return HttpResponse.json(
          { code: "TASK_NOT_FOUND", message: "not a task" },
          { status: 404 },
        );
      }
      // opres-v2 has no anchor↔anchor edges — the empty tab is the truth.
      return HttpResponse.json({ findings: [] });
    },
  ),

  http.get(
    "*/api/workstreams/:workstreamId/tasks/:nodeId/draft",
    ({ params }) => {
      const nodeId = params.nodeId as string;
      if (!TASKS[nodeId]) {
        return HttpResponse.json(
          { code: "TASK_NOT_FOUND", message: `${nodeId} is not a task` },
          { status: 404 },
        );
      }
      return HttpResponse.json<DraftResponse>({
        node_id: nodeId,
        content_html: draftHtml,
        last_saved_at: draftSavedAt,
      });
    },
  ),

  http.put(
    "*/api/workstreams/:workstreamId/tasks/:nodeId/draft",
    async ({ request, params }) => {
      const body = (await request.json()) as { content_html: string };
      draftHtml = body.content_html;
      draftSavedAt = "2026-07-15T09:00:00Z";
      return HttpResponse.json<DraftResponse>({
        node_id: params.nodeId as string,
        content_html: draftHtml,
        last_saved_at: draftSavedAt,
      });
    },
  ),

  http.post(
    "*/api/workstreams/:workstreamId/tasks/:nodeId/copilot",
    async ({ request }) => {
      const body = (await request.json()) as {
        intent: CopilotIntent;
        message?: string;
        history?: { role: string; text: string }[];
        referenced_finding_ids?: string[];
      };
      const script = COPILOT_SCRIPT[body.intent];
      if (!script) {
        return HttpResponse.json(
          { code: "INVALID_INTENT", message: `bad intent ${body.intent}` },
          { status: 400 },
        );
      }
      if (!body.message || !body.message.trim()) {
        return HttpResponse.json(
          { code: "MESSAGE_REQUIRED", message: "message must be non-empty" },
          { status: 400 },
        );
      }
      // Mirrors the live server holding no conversation state: the mock keys
      // its scripted reply off how many copilot turns already appear in the
      // history the client sent, not a client-owned counter.
      const turn = (body.history ?? []).filter((m) => m.role === "copilot").length;
      const index = Math.min(turn, script.length - 1);
      return HttpResponse.json({ reply: script[index] });
    },
  ),

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
      return HttpResponse.json({
        ...task,
        workflow: taskWorkflow.get(nodeId) ?? task.workflow,
      });
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
  http.patch(
    "*/api/workstreams/:workstreamId/tasks/:nodeId/workflow",
    async ({ params, request }) => {
      const { nodeId } = params as { nodeId: string };
      if (!(nodeId in TASKS)) {
        return jsonError(400, "NOT_A_TASK", `Node ${nodeId} is not a task`);
      }
      const body = (await request.json()) as {
        status?: string;
        actor_id?: string;
      };
      if (
        body.status !== "draft" &&
        body.status !== "pending_review" &&
        body.status !== "approved"
      ) {
        return jsonError(
          400,
          "INVALID_WORKFLOW_STATE",
          `status must be draft|pending_review|approved, got ${body.status}`,
        );
      }
      const actor = DIRECTORY.find((p) => p.id === body.actor_id);
      if (!actor) {
        return jsonError(
          400,
          "INVALID_ACTOR",
          `actor_id ${body.actor_id} is not in the directory`,
        );
      }
      const previous = taskWorkflow.get(nodeId) ?? TASKS[nodeId].workflow;
      const workflow: TaskWorkflow = { ...previous, status: body.status };
      if (body.status === "pending_review") workflow.checker = actor;
      if (body.status === "approved") {
        workflow.approved_by = actor;
        workflow.approved_at = "2026-07-19T09:00:00Z";
      }
      taskWorkflow.set(nodeId, workflow);
      return HttpResponse.json({ workflow });
    },
  ),
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
    return HttpResponse.json({
      workstreams: [...WORKSTREAMS, ...createdWorkstreams],
    });
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
