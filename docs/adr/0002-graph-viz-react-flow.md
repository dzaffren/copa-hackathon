# 2. Workspace graph rendering: React Flow

Date: 2026-07-10
Status: Accepted

## Context

The single-draft workspace (#7) renders the technology-risk cluster as an
interactive node/edge graph: policy nodes, external-reference nodes, and one
greyed cross-cluster preview node, with **clickable nodes and edges** that open a
detail panel ("why these are connected", "why this reference matters", "why this
changed"). The frontend is a React 18 + TypeScript SPA. The graph is tiny (≈7
policy nodes + a handful of reference nodes + a preview node) and non-physics —
layout can be curated.

## Decision

Use **React Flow (`reactflow`)** for the workspace graph. Custom node components
render the ring/treatment states (editable draft, published, superseded, reference,
locked, preview); edge click handlers drive the detail panel; a curated static
layout positions the single editable draft (RMiT v2) at the centre with references
orbiting it.

## Consequences

- First-class React integration (custom nodes/edges as components), built-in
  pan/zoom and click handling, minimal glue for a small graph.
- Adds one npm dependency (`reactflow`) to the `web/` project.
- Layout is curated (fixed positions), which suits a locked 7-node demo cluster
  and keeps the "editable draft at the centre" composition stable.

## Alternatives considered

- **d3-force / custom SVG.** Maximum control, no dependency, but re-implements
  hit-testing, pan/zoom, and node/edge components by hand — more effort for no
  MVP1 benefit on a tiny curated graph.
- **A heavyweight graph library (cytoscape, sigma).** Built for large/physics
  graphs; overkill here and heavier React integration.
