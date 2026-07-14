# 1. Drafter workflow state: browser localStorage for the demo, server-side for production

Date: 2026-07-10
Status: Accepted

## Context

The drafter experience (Draft alignment #8, Drafting copilot #9) shares mutable
**workflow state**: each finding's status (open / accepted / dismissed + reason),
the tracked-change markers an accepted fix inserts into the living draft, and the
open/resolved counts both pages show. Accepting a fix on one page must update the
other **live**. This state is deliberately separate from the engine's immutable,
rebuildable artifacts (`clause-index.json`, `graph.json`) — a corpus rebuild must
never touch in-flight workflow state.

The build is a hackathon MVP1 (single machine, single drafter, demo on 3 Aug 2026).
The clickable POC already implements this state in `localStorage` with cross-tab
sync via the `storage` event.

## Decision

For **MVP1**, drafter workflow state lives in the browser (`localStorage`), with
cross-tab live sync via the `window` `storage` event — the pattern the POC proved.
The React SPA owns it behind a single `web/src/lib/workflowState.ts` module so the
store is swappable.

The **production** path is a server-side workflow-state store keyed per document
and version (findings, lifecycle, tracked changes), fronted by the same
`workflowState` interface. It is documented in the specs but **not built for MVP1**.

## Consequences

- The demo is single-machine: state does not survive a different browser/device.
  Acceptable for the hackathon; called out explicitly in the pitch.
- The engine stays a pure read service over immutable artifacts — no workflow
  writes, no DB — preserving its rebuild-anytime property.
- Swapping to the server store later is an implementation change behind the
  `workflowState` module, not a rewrite of #8/#9.

## Alternatives considered

- **Server-side store now.** More faithful (multi-device, durable) but reopens the
  engine or adds a sibling service and build scope before the hackathon — rejected
  for MVP1, kept as the production path.
- **In-memory only (no persistence).** Simpler but loses the cross-page/cross-tab
  live-sync the POC relies on and the "resume where you left off" demo beat.
