// Node detail (spec-drafter-workspace.md · "Inspecting my editable draft",
// "Published BNM policies offer no editing action", "An external reference node
// shows that it exists and why it matters", "The Regulatory Handbook reference
// is a locked, content-withheld placeholder", "The AML/CFT cross-cluster node is
// preview only"; Validation & Business Rules).
//
// Given a selected node it shows the DERIVED treatment (never hand-set), the
// version, a short note, a "Linked to" list, and EXACTLY ONE action appropriate
// to the node:
//   • the single editable draft (isEditable) → enabled "Open the draft";
//   • every other BNM policy → disabled "Read-only";
//   • a public external reference → a short "why this reference matters" note +
//     the enabled "See in the Reference Radar" hand-off (deep content is #26 —
//     no verbatim passage here);
//   • the restricted Regulatory Handbook → a LOCKED, content-withheld placeholder
//     with a disabled action — and it fetches NOTHING (never calls getClause);
//   • a trend/news preview or the cross-cluster AML node → a disabled action.
//
// The "Linked to" list is hydrated from GET /nodes/{id} (outgoing edges) for
// policy nodes only; reference/preview/cross-cluster nodes make no engine call,
// so a withheld reference stays fully content-free.

import { useEffect, useState } from "react";

import type { GraphNode, NodeDetailEdge } from "../../types";
import { getNode } from "../../lib/engineApi";
import {
  classifyNode,
  deriveMarking,
  EDITABLE_DRAFT_ID,
  isEditable,
  type TreatmentKind,
} from "../../lib/treatments";
import ProvenanceTrail from "./ProvenanceTrail";

export interface NodeDetailProps {
  node: GraphNode;
}

/** Treatments that are internal policy nodes — the only ones with a linked-to
 *  list worth fetching from the engine. */
const POLICY_TREATMENTS: ReadonlySet<TreatmentKind> = new Set([
  "editable-draft",
  "published-draft",
  "superseded",
  "in-force",
]);

interface ActionSpec {
  label: string;
  enabled: boolean;
}

/** The single action shown for a node — enabled only for the editable draft and
 *  the Reference Radar hand-off; every read-only / restricted / preview /
 *  cross-cluster action is visibly disabled. */
function actionFor(treatment: TreatmentKind): ActionSpec {
  switch (treatment) {
    case "editable-draft":
      return { label: "Open the draft", enabled: true };
    case "reference":
      return { label: "See in the Reference Radar", enabled: true };
    case "reference-restricted":
      return { label: "Restricted", enabled: false };
    case "reference-preview":
      return { label: "Preview", enabled: false };
    case "cross-cluster":
      return { label: "Outside your cluster · preview only", enabled: false };
    case "published-draft":
    case "superseded":
    case "in-force":
    default:
      return { label: "Read-only", enabled: false };
  }
}

/** A short, treatment-appropriate note for the node. */
function noteFor(node: GraphNode, treatment: TreatmentKind): string {
  switch (treatment) {
    case "editable-draft":
      return (
        "This is your single working draft — the only document you can edit " +
        "in this workspace. Every other policy here is published context."
      );
    case "superseded":
      return (
        "Published, read-only history — the superseded previous version. You " +
        "can read it but not edit or comment on its text."
      );
    case "published-draft":
    case "in-force":
      return (
        "Published, read-only context. You can read this policy but not edit " +
        "or comment on its text."
      );
    case "reference-restricted":
      return (
        "Restricted — access-controlled, like internal committee minutes. Its " +
        "guidance content is withheld here; only that it connects to your " +
        "draft is shown."
      );
    case "reference-preview":
      return (
        "An external signal shown as a preview. The trends & news layer is not " +
        "yet built; it joins the MVP only if more drafters confirm the need."
      );
    case "cross-cluster":
      return (
        "A change in RMiT touched this node, but it sits outside the " +
        "technology-risk cluster, so it surfaces here as a preview only. Full " +
        "cross-cluster mapping is a future phase."
      );
    case "reference":
    default:
      return referenceWhyItMatters(node);
  }
}

/** The public-reference "why this reference matters" note. Keyed by the engine
 *  `source_type` — the deep, clause-by-clause detail is the Reference Radar's
 *  (#26), never shown here. */
function referenceWhyItMatters(node: GraphNode): string {
  switch (node.source_type) {
    case "peer_regulator":
      return (
        "A peer regulator's equivalent technology-risk policy — a benchmark " +
        "for how another supervisor governs the same rules your clause changes."
      );
    case "act":
      return (
        "A national act whose legal limits your draft must respect — for " +
        "example the limits on transferring personal data to cloud regions " +
        "abroad."
      );
    case "standard":
      return (
        "An international standard that sets the baseline your draft should " +
        "stay aligned with for third-party and cloud dependencies."
      );
    default:
      return "An external reference connected to your draft.";
  }
}

type LinkStatus = "idle" | "loading" | "loaded" | "error";

interface LinkState {
  status: LinkStatus;
  edges: NodeDetailEdge[];
}

export default function NodeDetail({ node }: NodeDetailProps): JSX.Element {
  const treatment = classifyNode(node);
  const marking = deriveMarking(node);
  const editable = isEditable(node);
  const action = actionFor(treatment);
  const note = noteFor(node, treatment);
  const isPolicy = POLICY_TREATMENTS.has(treatment);
  const isReferencePublic = treatment === "reference";

  const [links, setLinks] = useState<LinkState>(() => ({
    status: isPolicy ? "loading" : "idle",
    edges: [],
  }));

  useEffect(() => {
    if (!isPolicy) {
      setLinks({ status: "idle", edges: [] });
      return;
    }

    let cancelled = false;
    setLinks({ status: "loading", edges: [] });
    getNode(node.id)
      .then((detail) => {
        if (!cancelled) setLinks({ status: "loaded", edges: detail.edges });
      })
      .catch(() => {
        // Never blank the panel on a failed convenience fetch — the header,
        // action and (for the draft) trail still render from the passed node.
        if (!cancelled) setLinks({ status: "error", edges: [] });
      });

    return () => {
      cancelled = true;
    };
  }, [node.id, isPolicy]);

  return (
    <div className="space-y-4">
      <header>
        <p
          data-testid="node-marking"
          className="text-xs font-semibold uppercase tracking-wide text-emerald-700"
        >
          {marking}
        </p>
        <h2 className="mt-1 text-base font-semibold text-slate-900">
          {node.title}
        </h2>
        <p className="text-sm text-slate-500">{node.version}</p>
        {isPolicy && (
          <p className="mt-1 text-xs text-slate-500">
            Derived status:{" "}
            <span className="text-slate-700">{node.status}</span>
          </p>
        )}
      </header>

      <p className="text-sm leading-relaxed text-slate-700">{note}</p>

      {isReferencePublic && (
        <section
          aria-labelledby="why-reference-heading"
          className="rounded-md bg-sky-50 p-3"
        >
          <h3
            id="why-reference-heading"
            className="text-xs font-semibold uppercase tracking-wide text-sky-700"
          >
            Why this reference matters
          </h3>
          <p className="mt-1 text-sm text-sky-900">
            External reference connected to your draft (RMiT v2). The verbatim,
            clause-by-clause detail lives in the Reference Radar — not shown
            here.
          </p>
        </section>
      )}

      {isPolicy && (
        <section aria-labelledby="linked-to-heading">
          <h3
            id="linked-to-heading"
            className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500"
          >
            Linked to
          </h3>
          {links.status === "loading" && (
            <p className="text-sm text-slate-400">Loading linked policies…</p>
          )}
          {links.status === "error" && (
            <p className="text-sm text-slate-400">
              Could not load linked policies.
            </p>
          )}
          {links.status === "loaded" && links.edges.length === 0 && (
            <p className="text-sm text-slate-400">No linked policies.</p>
          )}
          {links.status === "loaded" && links.edges.length > 0 && (
            <ul className="space-y-2">
              {links.edges.map((edge) => (
                <li
                  key={edge.target}
                  data-testid={`linked-to-${edge.target}`}
                  className="text-sm text-slate-700"
                >
                  {edge.reason}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {node.id === EDITABLE_DRAFT_ID && (
        <ProvenanceTrail documentId={EDITABLE_DRAFT_ID} />
      )}

      <div className="border-t border-slate-200 pt-4">
        <button
          type="button"
          disabled={!action.enabled}
          aria-disabled={!action.enabled}
          className={
            action.enabled
              ? "rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white"
              : "cursor-not-allowed rounded border border-slate-300 bg-slate-100 px-4 py-2 text-sm font-medium text-slate-400"
          }
        >
          {action.label}
        </button>
        {editable && (
          <p className="mt-1 text-xs text-slate-400">
            Approval is a separate manager step, never offered here.
          </p>
        )}
      </div>
    </div>
  );
}
