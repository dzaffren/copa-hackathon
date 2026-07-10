# 5. Copilot write-back: mock tracked change for MVP1, Microsoft Graph for production

Date: 2026-07-10
Status: Accepted

## Context

When a drafter accepts a copilot redraft, it is written into the living working
document as a **tracked change** (old wording struck through, new wording inserted)
for a human to accept or reject — "AI proposes, human commits". In production the
living document is a Word file on SharePoint, written via Microsoft Graph. A real
Graph integration needs a tenant, app registration, and delegated permissions —
heavy for a 3 Aug 2026 hackathon demo with no supervised-entity data at stake on
the drafter path.

## Decision

For **MVP1**, the living draft is rendered by a mock Word-style viewer
(`web/src/components/DraftDocViewer.tsx`), and an accepted redraft is persisted as
a tracked change in `localStorage` (`rulebook-radar:tracked-changes`) with status
always `"pending"` — a human accepts or rejects it in the viewer; the copilot never
finalises text. The change is shared with #8's finding state so both pages sync
live (see ADR 0001).

The **production** path writes the tracked change into the SharePoint Word document
via Microsoft Graph, behind the same `DraftDocViewer` / `workflowState` interface.

## Consequences

- No tenant, app registration, or credentials needed for the demo; the full
  closed-loop UX (propose → tracked change → human commit → finding resolved →
  cross-page sync) works entirely locally.
- "AI proposes, human commits" is preserved exactly — the mock still requires a
  human accept/reject before anything is "final".
- The real Graph integration is a documented swap behind one component + the
  workflow-state module, not a rewrite of #9.

## Alternatives considered

- **Real Microsoft Graph write-back now.** Faithful, but needs a SharePoint tenant
  and app credentials and adds integration scope before the hackathon — rejected
  for MVP1, kept as production.
- **No write-back (show the redraft only in chat).** Loses the closed-loop demo
  beat (accepted fix appears in the document as a tracked change) that makes the
  "AI proposes, human commits" story tangible. Rejected.
