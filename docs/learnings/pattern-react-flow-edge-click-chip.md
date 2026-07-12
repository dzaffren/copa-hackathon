---
name: react-flow-edge-click-chip
description: Make React Flow edges reliably E2E-clickable via a testid'd midpoint chip, not a wide hit path
type: pattern
captured: 2026-07-12
source: /build session (#7 single-draft Rulebook Workspace, web/ cluster map)
---

To make a React Flow edge a reliable click target in Playwright E2E, render a
compact midpoint "why" chip that carries
`data-testid="edge-{source}__{target}"`, keep the transparent interaction
path narrow (`interactionWidth` ~10, i.e. `INTERACTION_WIDTH = 10` in
`web/src/components/graph/edgeTypes.tsx`), and use a deterministic paint-order
so overlapping bands do not steal the click. Do NOT rely on a wide transparent
edge path as the hit target.

**Why:** Thin curved bezier edge paths overlap on the map, and a wide
(`strokeWidth 20`) transparent interaction area lets one edge's hit-region
sweep across a neighbour's, so clicks meant for one edge land on another and
E2E specs (e.g. `connection-detail.spec.ts`) flake. A solid, centred midpoint
chip is a dedicated, deterministic hit point that bubbles to React Flow's
`onEdgeClick`, so selection is unchanged but tests are stable.

**How to apply:** Any `web/` story that adds edge-click behaviour or E2E to the
cluster map (e.g. #8 ripple, #9 copilot) should reuse the `ClusterEdge`
midpoint-chip pattern and the `edge-{source}__{target}` testid convention
rather than widening the interaction stroke. Keep clause/"why" text off the
map itself — the explanation belongs to the detail panel.
