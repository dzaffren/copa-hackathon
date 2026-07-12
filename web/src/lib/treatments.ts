// Treatment deriver — turns an engine `GraphNode` into the observable "marking"
// the workspace shows on each node (spec-drafter-workspace.md · "Each node's
// marking matches its derived treatment" + Test 2).
//
// PURELY DERIVED. The marking is computed only from engine fields — `status`,
// `kind`, `access`, `preview`, `cluster` — never from a node id, title, or any
// hand-set field. This enforces the business rule "Status is derived, not
// entered": there is no marking string a caller can override.

import type { GraphNode } from "../types";

/** The one cluster this MVP1 workspace maps; anything else is cross-cluster. */
const TECHNOLOGY_RISK_CLUSTER = "technology-risk";

/**
 * The single editable draft's node id — the workspace's single-draft identity.
 * This is NOT a hand-set marking field: it is the one document this drafter owns
 * (spec line 609 "Only `rmit-v2-2026-draft` may show the `your draft — you edit`
 * treatment", and the auto-select id at line 578). The real corpus has TWO
 * `status:"In progress"` nodes — this draft and BNM's published "Discussion
 * Paper 2025" (Operational Resilience) — so status alone cannot tell them apart;
 * the editable one is identified by this id. Task 7/8 reuse it to gate the one
 * enabled "Open the draft" action.
 */
export const EDITABLE_DRAFT_ID = "rmit-v2-2026-draft";

/**
 * The mutually-exclusive treatment categories a node can fall into. `graphModel`
 * uses this to pick a React Flow node renderer; `deriveMarking` maps it to the
 * exact on-screen string.
 */
export type TreatmentKind =
  | "editable-draft" // the single editable draft (RMiT v2) — identified by id, the only editable node
  | "published-draft" // an in-progress node that is NOT the user's draft (e.g. a published Discussion Paper) — read-only
  | "superseded" // a published, read-only previous version
  | "in-force" // a published, read-only current policy
  | "cross-cluster" // a node from another cluster (AML/CFT) — preview only
  | "reference" // an external reference (public), deep content handled by #26
  | "reference-restricted" // a restricted reference (Regulatory Handbook) — locked
  | "reference-preview"; // a labelled preview signal (trend/news/foreign policy)

/**
 * Classify a node into its treatment kind, purely from engine fields plus the
 * workspace's single editable-draft id.
 *
 * Order matters: reference-kind nodes are resolved first (preview beats
 * restricted beats public), then cross-cluster membership, then the published
 * lifecycle status. Of the two `status:"In progress"` nodes in the real corpus,
 * only the one whose id matches `editableDraftId` is the user's editable draft;
 * the other (a published Discussion Paper) is read-only `published-draft`
 * context. This upholds "only RMiT v2 is editable" without hand-setting a
 * marking field — the id is the document's identity, not a marking.
 */
export function classifyNode(
  node: GraphNode,
  editableDraftId: string = EDITABLE_DRAFT_ID,
): TreatmentKind {
  if (node.kind === "reference") {
    if (node.preview === true) return "reference-preview";
    if (node.access === "restricted") return "reference-restricted";
    return "reference";
  }

  if (node.cluster && node.cluster !== TECHNOLOGY_RISK_CLUSTER) {
    return "cross-cluster";
  }

  switch (node.status) {
    case "In progress":
      // Two nodes carry "In progress": the user's editable draft (RMiT v2) and
      // BNM's published "Discussion Paper 2025" (Operational Resilience). Only
      // the editable-draft id is the user's to edit; every other in-progress
      // node is published, read-only context.
      return node.id === editableDraftId ? "editable-draft" : "published-draft";
    case "Superseded":
      return "superseded";
    case "In force":
      return "in-force";
    default:
      // Unknown status → treat as read-only in-force so nothing becomes
      // accidentally editable. (No engine status other than the three above
      // is produced today; this is a defensive fallback.)
      return "in-force";
  }
}

/** The exact observable marking string for each treatment kind. These strings
 *  are contractual — they appear verbatim in the spec's Acceptance Criteria
 *  (Scenario Outline "Each node's marking matches its derived treatment") and in
 *  Test 2, and are asserted by the E2E `data-marking` locators. */
const MARKINGS: Record<TreatmentKind, string> = {
  "editable-draft": "your draft — you edit",
  "published-draft": "published · draft (read-only)",
  superseded: "published · superseded (read-only history)",
  "in-force": "published · in force (read-only)",
  "cross-cluster": "other cluster (preview only)",
  reference: "external reference",
  "reference-restricted": "external reference · restricted (locked)",
  "reference-preview": "external signal · preview",
};

/** Derive the on-screen marking for a node, purely from its engine fields plus
 *  the workspace's editable-draft id (defaults to `EDITABLE_DRAFT_ID`). */
export function deriveMarking(
  node: GraphNode,
  editableDraftId: string = EDITABLE_DRAFT_ID,
): string {
  return MARKINGS[classifyNode(node, editableDraftId)];
}

/** True only for the single editable draft (the node whose id is
 *  `editableDraftId`). The detail panel uses this to gate the one enabled "Open
 *  the draft" action; every other node — including a published in-progress
 *  Discussion Paper — renders a disabled read-only/restricted/preview action. */
export function isEditable(
  node: GraphNode,
  editableDraftId: string = EDITABLE_DRAFT_ID,
): boolean {
  return classifyNode(node, editableDraftId) === "editable-draft";
}
