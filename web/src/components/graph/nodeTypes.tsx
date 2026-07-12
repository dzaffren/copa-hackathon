// Custom React Flow node renderers for the cluster map (spec-drafter-workspace.md
// · UI/Frontend Requirements "The cluster map … Each node carries a visible
// state"). One treatment-driven renderer covers every marking: policy nodes
// (editable draft / published draft / in force / superseded), external-reference
// nodes (public / restricted), and preview nodes (cross-cluster + trend/news).
//
// Contract (Verification → Locator strategies): every node's root element carries
//   • data-testid="node-{id}"  — the E2E locator
//   • data-marking="{marking}"  — the derived treatment string
// The marking is NEVER hardcoded here: it is computed by `deriveMarking` and the
// ring/band styling by `classifyNode`, both pure functions of the engine node
// (treatments.ts). This upholds "Status is derived, not entered".

import { Handle, Position, type NodeProps, type NodeTypes } from "reactflow";
import type { CSSProperties } from "react";

import {
  classifyNode,
  deriveMarking,
  type TreatmentKind,
} from "../../lib/treatments";
import type { RFNodeData } from "../../lib/graphModel";

/** Every treatment kind, in a sensible legend / rendering order. */
export const TREATMENT_KINDS: TreatmentKind[] = [
  "editable-draft",
  "published-draft",
  "in-force",
  "superseded",
  "reference",
  "reference-restricted",
  "reference-preview",
  "cross-cluster",
];

/** Per-treatment visual treatment: a legend swatch class + the node card class. */
export interface TreatmentStyle {
  /** Small coloured swatch used on the node and in the legend. */
  swatchClass: string;
  /** Card border / background / text classes. */
  cardClass: string;
}

/** Ring / band / lock styling per `classifyNode` result. Indicative colours for
 *  the demo (the spec calls exact styling non-contractual); the observable
 *  contract is the `data-marking` string, not these classes. */
export const TREATMENT_STYLES: Record<TreatmentKind, TreatmentStyle> = {
  // Green ring around the single editable draft — visually the centre.
  "editable-draft": {
    swatchClass: "bg-emerald-500",
    cardClass:
      "border-2 border-emerald-500 ring-2 ring-emerald-200 bg-white text-slate-800",
  },
  // A published in-progress discussion paper — read-only, amber accent.
  "published-draft": {
    swatchClass: "bg-amber-400",
    cardClass: "border border-amber-300 bg-white text-slate-700",
  },
  // Published, in force — plain read-only corpus treatment (no ring).
  "in-force": {
    swatchClass: "bg-slate-500",
    cardClass: "border border-slate-300 bg-white text-slate-700",
  },
  // Published, superseded — a muted, dashed history treatment.
  superseded: {
    swatchClass: "bg-slate-400",
    cardClass:
      "border border-dashed border-slate-400 bg-slate-50 text-slate-500",
  },
  // External reference (public) — a distinct reference-source treatment.
  reference: {
    swatchClass: "bg-sky-500",
    cardClass: "border border-sky-300 bg-sky-50 text-slate-700",
  },
  // External reference · restricted — a locked, withheld treatment.
  "reference-restricted": {
    swatchClass: "bg-sky-900",
    cardClass:
      "border border-dashed border-sky-400 bg-slate-100 text-slate-500",
  },
  // External signal · preview — a labelled "not yet built" preview treatment.
  "reference-preview": {
    swatchClass: "bg-violet-400",
    cardClass:
      "border-2 border-dashed border-violet-400 bg-violet-50 text-slate-500",
  },
  // Other cluster (AML/CFT) — greyed, dashed, clearly non-actionable.
  "cross-cluster": {
    swatchClass: "bg-zinc-400",
    cardClass:
      "border-2 border-dashed border-zinc-400 bg-zinc-100 text-slate-500",
  },
};

/** Treatments that expose NO action at all in the detail panel — surfaced on the
 *  map as a non-actionable affordance (`aria-disabled` / `data-disabled`). */
const NON_ACTIONABLE: ReadonlySet<TreatmentKind> = new Set<TreatmentKind>([
  "cross-cluster",
  "reference-restricted",
  "reference-preview",
]);

/** Reference-family treatments (drive the "external reference" hint + handles). */
const REFERENCE_KINDS: ReadonlySet<TreatmentKind> = new Set<TreatmentKind>([
  "reference",
  "reference-restricted",
  "reference-preview",
]);

const HIDDEN_HANDLE: CSSProperties = { opacity: 0, pointerEvents: "none" };

/**
 * The single treatment-driven node renderer. It reads only `data.node` (the raw
 * engine node) and derives its marking + treatment, so it renders correctly no
 * matter which of the three React Flow node types (`policy` / `reference` /
 * `preview`) selected it.
 */
export function TreatmentNode({ data, selected }: NodeProps<RFNodeData>) {
  const node = data.node;
  const treatment = classifyNode(node);
  const marking = deriveMarking(node);
  const style = TREATMENT_STYLES[treatment];
  const nonActionable = NON_ACTIONABLE.has(treatment);
  const isReference = REFERENCE_KINDS.has(treatment);

  return (
    <div
      data-testid={`node-${node.id}`}
      data-marking={marking}
      data-treatment={treatment}
      data-selected={selected ? "true" : undefined}
      data-disabled={nonActionable ? "true" : undefined}
      aria-disabled={nonActionable || undefined}
      className={[
        "w-44 rounded-lg px-3 py-2 text-left shadow-sm transition-shadow",
        style.cardClass,
        selected ? "ring-2 ring-offset-1 ring-blue-500" : "",
      ].join(" ")}
    >
      {/* Invisible handles so edges anchor cleanly; the map is read-only. */}
      <Handle
        type="target"
        position={Position.Top}
        isConnectable={false}
        style={HIDDEN_HANDLE}
      />

      <div className="flex items-center gap-2">
        <span
          className={`inline-block h-2.5 w-2.5 shrink-0 rounded-sm ${style.swatchClass}`}
          aria-hidden="true"
        />
        <span className="truncate text-xs font-semibold">{node.title}</span>
        {treatment === "reference-restricted" ? (
          <span aria-hidden="true" title="restricted">
            🔒
          </span>
        ) : null}
      </div>

      {node.version ? (
        <div className="mt-0.5 text-[11px] text-slate-500">{node.version}</div>
      ) : null}

      <div className="mt-1 text-[10px] font-medium uppercase tracking-wide text-slate-500">
        {marking}
      </div>

      {isReference ? (
        <div className="mt-0.5 text-[9px] font-medium uppercase tracking-wide text-sky-600">
          external references band
        </div>
      ) : null}

      <Handle
        type="source"
        position={Position.Bottom}
        isConnectable={false}
        style={HIDDEN_HANDLE}
      />
    </div>
  );
}

/**
 * React Flow node-type registry. `graphModel` maps every treatment onto one of
 * these three keys (`policy` / `reference` / `preview`); all three resolve to the
 * treatment-driven `TreatmentNode`, which re-derives the exact styling from the
 * node itself.
 */
export const nodeTypes: NodeTypes = {
  policy: TreatmentNode,
  reference: TreatmentNode,
  preview: TreatmentNode,
};
