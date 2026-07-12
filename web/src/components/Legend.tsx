// The cluster-map legend (spec-drafter-workspace.md · UI/Frontend Requirements
// "The cluster map with a legend"; User Workflow step 1 "a legend explaining what
// each marking means"). One row per treatment kind: its swatch (shared with the
// node renderer) plus the exact derived marking string.
//
// The labels are NOT hardcoded: each row's text is produced by `deriveMarking`
// over a representative node, so the legend can never drift from what the map
// actually shows.

import type { GraphNode } from "../types";
import {
  deriveMarking,
  EDITABLE_DRAFT_ID,
  type TreatmentKind,
} from "../lib/treatments";
import { TREATMENT_KINDS, TREATMENT_STYLES } from "./graph/nodeTypes";

/** A minimal node with the given overrides — just enough for `classifyNode` /
 *  `deriveMarking` to resolve the treatment. */
function baseNode(overrides: Partial<GraphNode>): GraphNode {
  return {
    id: "legend",
    policy_id: "legend",
    title: "legend",
    version: "",
    status: "In force",
    cluster: "technology-risk",
    ...overrides,
  };
}

/** A representative engine node for each treatment kind, so `deriveMarking`
 *  yields the exact on-screen marking string for the legend label. */
function representative(kind: TreatmentKind): GraphNode {
  switch (kind) {
    case "editable-draft":
      return baseNode({ id: EDITABLE_DRAFT_ID, status: "In progress" });
    case "published-draft":
      return baseNode({ id: "a-published-draft", status: "In progress" });
    case "in-force":
      return baseNode({ status: "In force" });
    case "superseded":
      return baseNode({ status: "Superseded" });
    case "reference":
      return baseNode({ kind: "reference", access: "public", preview: false });
    case "reference-restricted":
      return baseNode({
        kind: "reference",
        source_type: "handbook",
        access: "restricted",
        preview: false,
      });
    case "reference-preview":
      return baseNode({
        kind: "reference",
        source_type: "trend",
        access: "public",
        preview: true,
      });
    case "cross-cluster":
      return baseNode({ cluster: "aml-cft" });
  }
}

/** One legend row per treatment kind, with its derived marking string. Exported
 *  so the component test can drive its expectations from the same source. */
export const LEGEND_ROWS: { kind: TreatmentKind; marking: string }[] =
  TREATMENT_KINDS.map((kind) => ({
    kind,
    marking: deriveMarking(representative(kind)),
  }));

/** The marking legend for the cluster map. */
export default function Legend() {
  return (
    <section
      data-testid="legend"
      aria-label="Map legend"
      className="rounded-md border border-slate-200 bg-white/90 p-3 text-slate-700 shadow-sm"
    >
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
        Legend
      </h2>
      <ul className="space-y-1">
        {LEGEND_ROWS.map(({ kind, marking }) => (
          <li
            key={kind}
            data-testid={`legend-${kind}`}
            className="flex items-center gap-2"
          >
            <span
              className={`inline-block h-2.5 w-2.5 shrink-0 rounded-sm ${TREATMENT_STYLES[kind].swatchClass}`}
              aria-hidden="true"
            />
            <span className="text-[11px] leading-tight text-slate-600">
              {marking}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
