import { http, HttpResponse } from "msw";
import type { Connection, TaskResponse } from "@/lib/types";

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

function jsonError(status: number, code: string, message: string) {
  return HttpResponse.json({ code, message }, { status });
}

export const handlers = [
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
];

export { TASK_V0_3, TASK_V0_0, FINDINGS };
