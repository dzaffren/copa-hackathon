// Tests for the graph model mapper (spec-drafter-workspace.md · Test 2 markings
// on the mapped model + the "reference band tolerance" acceptance criterion:
// the AML preview and the external-reference band must render even when the
// engine graph has NO reference nodes, and real engine reference nodes must win
// over the overlay copies when present).

import { describe, expect, it } from "vitest";

import type { Graph, GraphNode } from "../types";
import { workspaceOverlay } from "../fixtures/workspaceOverlay";
import { toReactFlowModel, type RFNode } from "./graphModel";

/** The real technology-risk corpus (data/artifacts/graph.json), reference-free —
 *  so these tests exercise the "engine has not yet seeded references" path. */
const POLICY_GRAPH: Graph = {
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
      // Real corpus: this published Discussion Paper also carries "In progress"
      // — it must NOT be treated as the user's editable draft.
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
      source: "rmit-v2-2026-draft",
      target: "outsourcing-v1-2019",
      type: "overlaps",
      reason:
        "A public-cloud arrangement is often also a material outsourcing. " +
        "RMiT clause 17 interacts with Outsourcing 12.1 — the core conflict.",
      source_clauses: ["RMiT 17.1", "RMiT 17.2"],
      target_clauses: ["Outsourcing 12.1"],
      provenance: "curated",
      confidence: 1.0,
    },
    {
      source: "rmit-v1-2020",
      target: "rmit-v2-2026-draft",
      type: "version-lineage",
      reason: "rmit-v1-2020 is superseded by rmit-v2-2026-draft.",
      source_clauses: [],
      target_clauses: [],
      provenance: "structural",
      confidence: 1.0,
    },
  ],
};

/** Find a mapped node by its engine id. */
function nodeById(nodes: RFNode[], id: string): RFNode {
  const found = nodes.find((n) => n.id === id);
  if (!found) throw new Error(`node ${id} not in model`);
  return found;
}

describe("toReactFlowModel — engine nodes", () => {
  it("maps every engine policy node with its derived marking", () => {
    const { nodes } = toReactFlowModel(POLICY_GRAPH, workspaceOverlay);

    expect(nodeById(nodes, "rmit-v2-2026-draft").data.marking).toBe(
      "your draft — you edit",
    );
    expect(nodeById(nodes, "rmit-v1-2020").data.marking).toBe(
      "published · superseded (read-only history)",
    );
    expect(nodeById(nodes, "outsourcing-v1-2019").data.marking).toBe(
      "published · in force (read-only)",
    );
    // The second in-progress node is read-only context, NOT the user's draft.
    expect(nodeById(nodes, "opres-v1-2025-draft").data.marking).toBe(
      "published · draft (read-only)",
    );
  });

  it("puts the draft at the centre and exposes a node-{id} test id", () => {
    const { nodes } = toReactFlowModel(POLICY_GRAPH, workspaceOverlay);
    const draft = nodeById(nodes, "rmit-v2-2026-draft");
    expect(draft.position).toEqual({ x: 0, y: 0 });
    expect(draft.data.testId).toBe("node-rmit-v2-2026-draft");
  });

  it("is deterministic — identical positions across repeated calls", () => {
    const a = toReactFlowModel(POLICY_GRAPH, workspaceOverlay);
    const b = toReactFlowModel(POLICY_GRAPH, workspaceOverlay);
    expect(a.nodes.map((n) => [n.id, n.position])).toEqual(
      b.nodes.map((n) => [n.id, n.position]),
    );
  });

  it("labels an overlap edge from its reason and tags it, with an edge-{s}__{t} id", () => {
    const { edges } = toReactFlowModel(POLICY_GRAPH, workspaceOverlay);
    const edge = edges.find(
      (e) => e.id === "rmit-v2-2026-draft__outsourcing-v1-2019",
    );
    expect(edge).toBeDefined();
    expect(edge?.label).toContain("material outsourcing");
    expect(edge?.data?.edgeKind).toBe("overlap");
    expect(edge?.data?.targetClauses).toEqual(["Outsourcing 12.1"]);
    expect(edge?.data?.testId).toBe(
      "edge-rmit-v2-2026-draft__outsourcing-v1-2019",
    );
  });

  it("maps the structural version-lineage edge as its own kind", () => {
    const { edges } = toReactFlowModel(POLICY_GRAPH, workspaceOverlay);
    const lineage = edges.find(
      (e) => e.id === "rmit-v1-2020__rmit-v2-2026-draft",
    );
    expect(lineage?.data?.edgeKind).toBe("lineage");
  });
});

describe("toReactFlowModel — overlay merge (reference band tolerance)", () => {
  it("adds the AML cross-cluster preview node even though it is not an engine node", () => {
    const { nodes } = toReactFlowModel(POLICY_GRAPH, workspaceOverlay);
    const aml = nodeById(nodes, "aml-cft");
    expect(aml.data.marking).toBe("other cluster (preview only)");
    expect(aml.data.treatment).toBe("cross-cluster");
  });

  it("renders the whole external-reference band when the engine graph has none", () => {
    const { nodes } = toReactFlowModel(POLICY_GRAPH, workspaceOverlay);
    // No reference nodes came from the engine graph...
    expect(POLICY_GRAPH.nodes.some((n) => n.kind === "reference")).toBe(false);
    // ...but the mapped model has the full band from the overlay.
    for (const id of [
      "mas-trm-2021",
      "pdpa-2010",
      "basel-por-2021",
      "bnm-handbook",
      "trend-cloud-signals",
    ]) {
      expect(nodeById(nodes, id)).toBeDefined();
    }
    expect(nodeById(nodes, "pdpa-2010").data.marking).toBe(
      "external reference",
    );
    expect(nodeById(nodes, "bnm-handbook").data.marking).toBe(
      "external reference · restricted (locked)",
    );
    expect(nodeById(nodes, "trend-cloud-signals").data.marking).toBe(
      "external signal · preview",
    );
  });

  it("adds the dashed AML preview edge and the reference edges from the draft", () => {
    const { edges } = toReactFlowModel(POLICY_GRAPH, workspaceOverlay);

    const amlEdge = edges.find((e) => e.id === "rmit-v2-2026-draft__aml-cft");
    expect(amlEdge?.data?.edgeKind).toBe("cross-cluster");
    expect(amlEdge?.data?.preview).toBe(true);
    expect(amlEdge?.animated).toBe(true);

    const pdpaEdge = edges.find(
      (e) => e.id === "rmit-v2-2026-draft__pdpa-2010",
    );
    expect(pdpaEdge?.data?.edgeKind).toBe("reference");
    expect(pdpaEdge?.label).toContain("personal data");
  });

  it("does NOT duplicate a reference node the engine graph already provides", () => {
    // Engine seeds its own pdpa-2010 (real reference extension has landed).
    const enginePdpa: GraphNode = {
      id: "pdpa-2010",
      policy_id: "pdpa",
      title: "Personal Data Protection Act (PDPA) — from engine",
      version: "Act 709 · 2010",
      status: "In force",
      cluster: "technology-risk",
      kind: "reference",
      source_type: "act",
      access: "public",
      preview: false,
    };
    const withEngineRef: Graph = {
      nodes: [...POLICY_GRAPH.nodes, enginePdpa],
      edges: POLICY_GRAPH.edges,
    };

    const { nodes } = toReactFlowModel(withEngineRef, workspaceOverlay);
    const pdpaNodes = nodes.filter((n) => n.id === "pdpa-2010");
    expect(pdpaNodes).toHaveLength(1);
    // The engine node wins over the overlay copy.
    expect(pdpaNodes[0].data.title).toContain("from engine");
  });

  it("counts merged nodes = engine nodes + overlay nodes not already present", () => {
    const { nodes } = toReactFlowModel(POLICY_GRAPH, workspaceOverlay);
    expect(nodes).toHaveLength(
      POLICY_GRAPH.nodes.length + workspaceOverlay.nodes.length,
    );
  });
});
