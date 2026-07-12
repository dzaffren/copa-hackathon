// Workspace page (spec-drafter-workspace.md · System Design "Workspace page":
// "Owns selection state, loads graph, wires map ↔ detail panel"). This is the
// drafter's home at `/` and a pure READ client of the engine — it calls only
// `GET /graph` (via `getGraph`) and never `POST /connections/find` (that is #8).
//
// Behaviour bound to the scenarios / Functional Requirements:
//   • On mount it loads the graph and handles three states — loading (a simple
//     indicator), error (a labelled region, never a blank screen), and loaded.
//   • On load it AUTO-SELECTS the single editable draft `rmit-v2-2026-draft` so
//     the detail panel is never blank; if that id is absent (corpus
//     misconfiguration) it falls back to the first `technology-risk` node and
//     logs a console warning — never an empty panel.
//   • Node / edge clicks route to the detail panel; an empty-pane click is a
//     deliberate no-op that keeps the current selection.
//   • It renders NO approval / submit control — approval is a separate manager
//     step handled elsewhere.

import { useEffect, useMemo, useState } from "react";

import DetailPanel, { type DetailSelection } from "../components/DetailPanel";
import ClusterGraph from "../components/graph/ClusterGraph";
import WorkspaceStrip from "../components/WorkspaceStrip";
import { workspaceOverlay } from "../fixtures/workspaceOverlay";
import { EngineConfigError, getGraph } from "../lib/engineApi";
import { EDITABLE_DRAFT_ID } from "../lib/treatments";
import type { Graph, GraphEdge, GraphNode } from "../types";

/** The one cluster this MVP1 workspace maps; used for the auto-select fallback. */
const TECHNOLOGY_RISK_CLUSTER = "technology-risk";

type LoadState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "loaded"; graph: Graph };

/**
 * The node to auto-select once the graph loads: the single editable draft, else
 * the first technology-risk node (with a console warning), else `null`. This
 * upholds "the detail panel is never blank" even under a corpus misconfiguration,
 * while never inventing a selection when the graph is genuinely empty.
 */
function initialSelection(graph: Graph): DetailSelection {
  const draft = graph.nodes.find((node) => node.id === EDITABLE_DRAFT_ID);
  if (draft) return { kind: "node", node: draft };

  const fallback = graph.nodes.find(
    (node) => node.cluster === TECHNOLOGY_RISK_CLUSTER,
  );
  if (fallback) {
    console.warn(
      `WorkspacePage: '${EDITABLE_DRAFT_ID}' is absent from the graph; ` +
        `auto-selecting the first technology-risk node '${fallback.id}'.`,
    );
    return { kind: "node", node: fallback };
  }
  return null;
}

export default function WorkspacePage(): JSX.Element {
  const [load, setLoad] = useState<LoadState>({ status: "loading" });
  const [selection, setSelection] = useState<DetailSelection>(null);

  useEffect(() => {
    let cancelled = false;
    setLoad({ status: "loading" });
    getGraph()
      .then((graph) => {
        if (cancelled) return;
        setLoad({ status: "loaded", graph });
        setSelection(initialSelection(graph));
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setLoad({
          status: "error",
          message:
            error instanceof EngineConfigError
              ? error.message
              : "Could not load the workspace map from the engine. Check that " +
                "the engine read API is running and reachable, then reload.",
        });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const graph = load.status === "loaded" ? load.graph : null;

  // Resolve a clicked node / edge against the SAME merged set ClusterGraph renders
  // (the engine graph first, then the client overlay) so selecting an overlay
  // node — an external reference, the restricted handbook, the AML preview —
  // routes to its detail too. Engine entries win over overlay copies (first match
  // wins), mirroring graphModel's id-dedupe.
  const nodeById = useMemo(() => {
    const map = new Map<string, GraphNode>();
    if (graph) {
      for (const node of [...graph.nodes, ...workspaceOverlay.nodes]) {
        if (!map.has(node.id)) map.set(node.id, node);
      }
    }
    return map;
  }, [graph]);

  const edgeByEndpoints = useMemo(() => {
    const map = new Map<string, GraphEdge>();
    if (graph) {
      for (const edge of [...graph.edges, ...workspaceOverlay.edges]) {
        const key = `${edge.source}__${edge.target}`;
        if (!map.has(key)) map.set(key, edge);
      }
    }
    return map;
  }, [graph]);

  function handleNodeSelect(id: string): void {
    const node = nodeById.get(id);
    if (node) setSelection({ kind: "node", node });
  }

  function handleEdgeSelect(source: string, target: string): void {
    const edge = edgeByEndpoints.get(`${source}__${target}`);
    if (edge) setSelection({ kind: "edge", edge });
  }

  // An empty-pane click is a deliberate no-op: keep the current selection so the
  // detail panel never blanks ("Clicking empty map space keeps the current detail").
  function handlePaneClick(): void {
    /* intentionally empty — selection is preserved */
  }

  const selectedId = selection?.kind === "node" ? selection.node.id : undefined;

  return (
    <div className="flex h-screen flex-col bg-slate-50">
      <WorkspaceStrip />

      <div className="flex min-h-0 flex-1">
        {load.status === "loading" && (
          <div
            data-testid="workspace-loading"
            role="status"
            className="flex flex-1 items-center justify-center text-sm text-slate-500"
          >
            Loading the workspace map…
          </div>
        )}

        {load.status === "error" && (
          <div
            data-testid="workspace-error"
            role="alert"
            className="flex flex-1 items-center justify-center p-8"
          >
            <div className="max-w-md text-center">
              <h2 className="text-base font-semibold text-slate-900">
                The workspace map could not load
              </h2>
              <p className="mt-2 text-sm text-slate-600">{load.message}</p>
            </div>
          </div>
        )}

        {load.status === "loaded" && (
          <>
            <div className="relative min-w-0 flex-1">
              <ClusterGraph
                graph={load.graph}
                selectedId={selectedId}
                onNodeSelect={handleNodeSelect}
                onEdgeSelect={handleEdgeSelect}
                onPaneClick={handlePaneClick}
              />
            </div>
            <aside className="h-full w-96 shrink-0">
              <DetailPanel selection={selection} />
            </aside>
          </>
        )}
      </div>
    </div>
  );
}
