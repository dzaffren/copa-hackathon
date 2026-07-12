// Tests for the treatment deriver (spec-drafter-workspace.md · Test 2 "Derived
// markings"). Every marking string is asserted VERBATIM against the spec's
// Scenario Outline "Each node's marking matches its derived treatment", and the
// derivation is proven pure — it reads only engine fields, never a node id.

import { describe, expect, it } from "vitest";

import type { GraphNode } from "../types";
import {
  classifyNode,
  deriveMarking,
  EDITABLE_DRAFT_ID,
  isEditable,
} from "./treatments";

/** Build a policy node with sensible defaults; override per case. */
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

/** Build a reference node with sensible defaults; override per case. */
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

describe("deriveMarking — Test 2 exact strings", () => {
  it("marks the editable draft (status 'In progress') as 'your draft — you edit'", () => {
    const draft = policyNode({
      id: "rmit-v2-2026-draft",
      status: "In progress",
      version: "v2 · 2026 draft",
    });
    expect(deriveMarking(draft)).toBe("your draft — you edit");
  });

  it("marks a superseded node as 'published · superseded (read-only history)'", () => {
    const superseded = policyNode({ id: "rmit-v1-2020", status: "Superseded" });
    expect(deriveMarking(superseded)).toBe(
      "published · superseded (read-only history)",
    );
  });

  it("marks an in-force node as 'published · in force (read-only)'", () => {
    const inForce = policyNode({
      id: "outsourcing-v1-2019",
      status: "In force",
    });
    expect(deriveMarking(inForce)).toBe("published · in force (read-only)");
  });

  it("marks a cross-cluster node (cluster:'aml-cft') as 'other cluster (preview only)'", () => {
    const aml = policyNode({ id: "aml-cft", cluster: "aml-cft" });
    expect(deriveMarking(aml)).toBe("other cluster (preview only)");
  });

  it("marks a restricted handbook reference as 'external reference · restricted (locked)'", () => {
    const handbook = referenceNode({
      id: "bnm-handbook",
      source_type: "handbook",
      access: "restricted",
      preview: false,
    });
    expect(deriveMarking(handbook)).toBe(
      "external reference · restricted (locked)",
    );
  });
});

describe("deriveMarking — remaining reference cases (spec marking scenario)", () => {
  it("marks a public reference as 'external reference' (spec: PDPA row)", () => {
    const publicRef = referenceNode({
      id: "pdpa-2010",
      source_type: "act",
      access: "public",
      preview: false,
    });
    expect(deriveMarking(publicRef)).toBe("external reference");
  });

  it("marks a preview trend reference as 'external signal · preview' (spec: EU DORA row)", () => {
    const previewRef = referenceNode({
      id: "trend-cloud-signals",
      source_type: "trend",
      access: "public",
      preview: true,
    });
    expect(deriveMarking(previewRef)).toBe("external signal · preview");
  });

  it("prefers the preview treatment over access even for a restricted preview node", () => {
    const restrictedPreview = referenceNode({
      access: "restricted",
      preview: true,
    });
    expect(deriveMarking(restrictedPreview)).toBe("external signal · preview");
  });
});

describe("deriveMarking — the single editable draft is id-gated", () => {
  it("marks ONLY the editable-draft id as 'your draft — you edit'", () => {
    const draft = policyNode({
      id: EDITABLE_DRAFT_ID,
      status: "In progress",
      version: "v2 · 2026 draft",
    });
    expect(deriveMarking(draft)).toBe("your draft — you edit");
    expect(isEditable(draft)).toBe(true);
  });

  it("marks a NON-editable in-progress node (published Discussion Paper) as 'published · draft (read-only)'", () => {
    // opres-v1-2025-draft carries engine status "In progress" in the real
    // corpus but is BNM's published discussion paper, not the user's draft.
    const opres = policyNode({
      id: "opres-v1-2025-draft",
      status: "In progress",
      version: "draft · Discussion Paper 2025",
    });
    expect(classifyNode(opres)).toBe("published-draft");
    expect(deriveMarking(opres)).toBe("published · draft (read-only)");
    expect(isEditable(opres)).toBe(false);
  });

  it("read-only policy markings do not depend on id (two in-force nodes match)", () => {
    const a = policyNode({ id: "outsourcing-v1-2019", status: "In force" });
    const b = policyNode({
      id: "recovery-planning-v1-2021",
      status: "In force",
    });
    expect(deriveMarking(a)).toBe(deriveMarking(b));
  });

  it("treats every node other than the editable draft as non-editable", () => {
    expect(isEditable(policyNode({ status: "In force" }))).toBe(false);
    expect(isEditable(policyNode({ status: "Superseded" }))).toBe(false);
    expect(isEditable(referenceNode({ access: "restricted" }))).toBe(false);
    expect(isEditable(policyNode({ cluster: "aml-cft" }))).toBe(false);
    expect(
      isEditable(
        policyNode({ id: "opres-v1-2025-draft", status: "In progress" }),
      ),
    ).toBe(false);
  });
});

describe("deriveMarking — pure over (node + editableDraftId)", () => {
  const inProgress = policyNode({
    id: "opres-v1-2025-draft",
    status: "In progress",
  });

  it("is parametric: passing a node's own id as editableDraftId makes it the draft", () => {
    expect(deriveMarking(inProgress, "opres-v1-2025-draft")).toBe(
      "your draft — you edit",
    );
    expect(isEditable(inProgress, "opres-v1-2025-draft")).toBe(true);
  });

  it("is parametric: an in-progress draft is read-only under a different draft id", () => {
    const draft = policyNode({ id: EDITABLE_DRAFT_ID, status: "In progress" });
    expect(deriveMarking(draft, "some-other-id")).toBe(
      "published · draft (read-only)",
    );
  });
});

describe("deriveMarking — real corpus has exactly one editable draft", () => {
  /** The seven real technology-risk policy nodes (data/artifacts/graph.json),
   *  including the TWO status:"In progress" nodes. */
  const realCorpus: GraphNode[] = [
    policyNode({ id: "rmit-v1-2020", status: "Superseded" }),
    policyNode({ id: "rmit-v2-2026-draft", status: "In progress" }),
    policyNode({ id: "outsourcing-v1-2019", status: "In force" }),
    policyNode({ id: "bcm-v1-2022", status: "In force" }),
    policyNode({ id: "opres-v1-2025-draft", status: "In progress" }),
    policyNode({ id: "recovery-planning-v1-2021", status: "In force" }),
    policyNode({ id: "customer-info-v1-2025", status: "In force" }),
  ];

  it("derives 'your draft — you edit' for exactly ONE node", () => {
    const drafts = realCorpus.filter(
      (n) => deriveMarking(n) === "your draft — you edit",
    );
    expect(drafts.map((n) => n.id)).toEqual(["rmit-v2-2026-draft"]);
  });

  it("marks the other in-progress node read-only, not editable", () => {
    const opres = realCorpus.find((n) => n.id === "opres-v1-2025-draft")!;
    expect(deriveMarking(opres)).toBe("published · draft (read-only)");
  });
});
