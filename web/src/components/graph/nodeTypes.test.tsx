// Tests for the custom node renderers (spec-drafter-workspace.md · Test 2 markings
// surfaced on the map + "Locator strategies": node root carries data-testid=
// "node-{id}" and data-marking="{marking}"). Each treatment must render the exact
// string `deriveMarking` produces — expectations are driven from `deriveMarking`
// so they can never diverge from treatments.ts.
//
// React Flow is mocked so <Handle> is a no-op and no ReactFlowProvider / canvas is
// needed; the renderer under test is `TreatmentNode`, which derives everything
// from the raw engine node in `data.node`.

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

// Stub reactflow: Handle → nothing, Position → the enum shape the node reads.
vi.mock("reactflow", () => ({
  Handle: () => null,
  Position: { Top: "top", Right: "right", Bottom: "bottom", Left: "left" },
}));

import type { NodeProps } from "reactflow";
import type { GraphNode } from "../../types";
import {
  classifyNode,
  deriveMarking,
  EDITABLE_DRAFT_ID,
} from "../../lib/treatments";
import type { RFNodeData } from "../../lib/graphModel";
import { nodeTypes, TreatmentNode } from "./nodeTypes";

/** A policy node with sensible defaults; override per case. */
function policyNode(overrides: Partial<GraphNode> = {}): GraphNode {
  return {
    id: "some-id",
    policy_id: "some-policy",
    title: "Some Policy",
    version: "v1 · 2020",
    status: "In force",
    cluster: "technology-risk",
    ...overrides,
  };
}

/** A reference node with sensible defaults; override per case. */
function referenceNode(overrides: Partial<GraphNode> = {}): GraphNode {
  return {
    id: "some-reference",
    policy_id: "some-reference",
    title: "Some Reference",
    version: "2021",
    status: "In force",
    cluster: "technology-risk",
    kind: "reference",
    source_type: "peer_regulator",
    access: "public",
    preview: false,
    ...overrides,
  };
}

/** Build the `data` payload exactly as `graphModel` would. */
function nodeData(node: GraphNode): RFNodeData {
  return {
    node,
    marking: deriveMarking(node),
    treatment: classifyNode(node),
    title: node.title,
    version: node.version,
    testId: `node-${node.id}`,
  };
}

/** Build minimal-but-typed NodeProps for the renderer under test. */
function nodeProps(node: GraphNode, selected = false): NodeProps<RFNodeData> {
  return {
    id: node.id,
    type: "policy",
    data: nodeData(node),
    selected,
  } as unknown as NodeProps<RFNodeData>;
}

const CASES: { name: string; node: GraphNode }[] = [
  {
    name: "editable-draft",
    node: policyNode({ id: EDITABLE_DRAFT_ID, status: "In progress" }),
  },
  {
    name: "published-draft (other in-progress node)",
    node: policyNode({ id: "opres-v1-2025-draft", status: "In progress" }),
  },
  {
    name: "superseded",
    node: policyNode({ id: "rmit-v1-2020", status: "Superseded" }),
  },
  {
    name: "in-force",
    node: policyNode({ id: "outsourcing-v1-2019", status: "In force" }),
  },
  {
    name: "cross-cluster",
    node: policyNode({ id: "aml-cft", cluster: "aml-cft" }),
  },
  {
    name: "reference (public)",
    node: referenceNode({ id: "pdpa-2010", source_type: "act" }),
  },
  {
    name: "reference-restricted",
    node: referenceNode({
      id: "bnm-handbook",
      source_type: "handbook",
      access: "restricted",
    }),
  },
  {
    name: "reference-preview",
    node: referenceNode({
      id: "trend-cloud-signals",
      source_type: "trend",
      preview: true,
    }),
  },
];

describe("TreatmentNode — data-testid + derived data-marking", () => {
  it.each(CASES)(
    "renders $name with node-{id} test id and the marking from deriveMarking",
    ({ node }) => {
      render(<TreatmentNode {...nodeProps(node)} />);
      const el = screen.getByTestId(`node-${node.id}`);
      expect(el).toBeInTheDocument();
      // Marking is exactly what treatments.ts derives — never a hardcoded string.
      expect(el).toHaveAttribute("data-marking", deriveMarking(node));
      // Treatment styling is driven by classifyNode.
      expect(el).toHaveAttribute("data-treatment", classifyNode(node));
      // The exact marking is visible on the card too.
      expect(el).toHaveTextContent(deriveMarking(node));
    },
  );
});

describe("TreatmentNode — non-actionable affordance", () => {
  it("marks cross-cluster / restricted / preview nodes as aria-disabled", () => {
    for (const node of [
      policyNode({ id: "aml-cft", cluster: "aml-cft" }),
      referenceNode({ id: "bnm-handbook", access: "restricted" }),
      referenceNode({ id: "trend-cloud-signals", preview: true }),
    ]) {
      const { unmount } = render(<TreatmentNode {...nodeProps(node)} />);
      const el = screen.getByTestId(`node-${node.id}`);
      expect(el).toHaveAttribute("aria-disabled", "true");
      expect(el).toHaveAttribute("data-disabled", "true");
      unmount();
    }
  });

  it("does NOT disable the editable draft or read-only policies", () => {
    const draft = policyNode({ id: EDITABLE_DRAFT_ID, status: "In progress" });
    render(<TreatmentNode {...nodeProps(draft)} />);
    const el = screen.getByTestId(`node-${draft.id}`);
    expect(el).not.toHaveAttribute("aria-disabled");
    expect(el).not.toHaveAttribute("data-disabled");
  });
});

describe("TreatmentNode — selection", () => {
  it("flags the node as selected when the selected prop is set", () => {
    const node = policyNode({ id: "outsourcing-v1-2019" });
    render(<TreatmentNode {...nodeProps(node, true)} />);
    expect(screen.getByTestId("node-outsourcing-v1-2019")).toHaveAttribute(
      "data-selected",
      "true",
    );
  });
});

describe("nodeTypes registry", () => {
  it("registers the treatment renderer under policy / reference / preview", () => {
    expect(nodeTypes.policy).toBe(TreatmentNode);
    expect(nodeTypes.reference).toBe(TreatmentNode);
    expect(nodeTypes.preview).toBe(TreatmentNode);
  });

  it("renders a node through the registered type", () => {
    const Comp = nodeTypes.reference;
    const node = referenceNode({ id: "mas-trm-2021" });
    render(<Comp {...nodeProps(node)} />);
    expect(screen.getByTestId("node-mas-trm-2021")).toHaveAttribute(
      "data-marking",
      deriveMarking(node),
    );
  });
});
