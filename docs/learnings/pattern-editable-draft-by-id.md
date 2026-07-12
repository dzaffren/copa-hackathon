---
name: editable-draft-by-id
description: Identify the single editable draft by node id (EDITABLE_DRAFT_ID), not by status — two nodes are "In progress"
type: pattern
captured: 2026-07-12
source: /build session (#7 single-draft Rulebook Workspace, web/ treatments)
---

The web workspace must identify the single editable draft by node id
(`EDITABLE_DRAFT_ID = "rmit-v2-2026-draft"`, in `web/src/lib/treatments.ts`),
never by engine `status`. The real corpus has TWO `status:"In progress"`
nodes — RMiT v2 (the editable draft) and the Operational Resilience 2025
Discussion Paper — so `deriveMarking` / `isEditable` are draft-id-aware:
the id-matched node renders `your draft — you edit`, and the other in-progress
node renders `published · draft (read-only)`.

**Why:** Status alone cannot distinguish the user's editable draft from a
published Discussion Paper, because both carry "In progress"
(`engine/tests/test_graph.py` asserts `opres-v1-2025` = "In progress"). Any
UI that derives a node's marking or editability by trusting `status` — or by
trusting the spec Background — will mislabel OpRes as editable or in-force.
The node id is the document's identity; the marking is purely derived from
engine fields plus that id, so nothing is hand-set.

**How to apply:** In any `web/` story that renders node markings or gates an
editable action (e.g. #8 ripple, #9 copilot, #10 supervisor), route the
decision through `classifyNode`/`isEditable` keyed on `EDITABLE_DRAFT_ID`, not
on `status`. Never assume exactly one "In progress" node.

**Follow-up (spec vs data divergence):** The spec Background of
`docs/specs/rulebook-radar/spec-drafter-workspace.md` (lines ~135, 203) lists
Operational Resilience as `published · in force (read-only)`, but the engine
emits `status:"In progress"` for it and the UI therefore shows
`published · draft (read-only)`. This is an unreconciled engine-data-vs-spec
divergence; a future spec or corpus edit should reconcile which state OpRes is
in. Until then, the id-based rule above is what the code relies on.
