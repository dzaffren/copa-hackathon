---
name: workstream-brain-opres-v2-conventions
description: build workstream-brain screens to the opres-v2 base (node_type/edge_type, derived analysed, task-as-edge-source), not the specs' greenfield shapes
type: convention
captured: 2026-07-15
source: /build session for spec-workstream-graph (PR #37); user chose to adapt to the base over the literal spec
---

Workstream-brain screens follow the **opres-v2 base conventions**, not the
specs' literal shapes. The workstream-brain specs (e.g.
`docs/specs/workstream-brain/spec-workstream-graph.md`) were authored greenfield
_before_ the Task Screen base (PR #36) landed, so their literal data shapes are
stale. The on-disk fixtures under `data/workstreams/` plus `engine/workstreams.py`
are the source of truth.

When building any further workstream-brain screen, adopt the base, **not** the
spec:

| Spec says (stale)             | Build to (opres-v2 base)                                                   |
| ----------------------------- | -------------------------------------------------------------------------- |
| workstream id `opres-2026`    | `opres-v2`                                                                 |
| node field `type`             | `node_type`                                                                |
| (edge field unspecified)      | `edge_type`                                                                |
| `analysed` stored on the edge | DERIVED: `true` iff `data/workstreams/{id}/findings/{edge_id}.json` exists |
| edges oriented anchor → PD    | edges oriented **task → anchor** (the task node is always the edge SOURCE) |

**Why:** the specs predate the merged base, and re-introducing their literal
`opres-2026`/`type` shapes would fork the fixtures and break cross-screen
navigation (the node "Open task" button must resolve to the existing task
screen). Task-as-source specifically: the Task Screen (`get_workstream_task`)
lists a task's **outgoing** edges only, so every on-disk edge points task →
anchor; `engine/workstreams.add_node` swaps orientation on add so a task is
never an edge target and a newly-added anchor still surfaces as a Task Screen
neighbour.

**How to apply:** when a workstream-brain spec names `opres-2026`, `type`, or a
stored `analysed`, treat those as stale and use the opres-v2 equivalents above.
Derive `analysed`/`findings_count` from the findings file, keep the task as the
edge source, and reuse `engine/workstreams.py` helpers rather than re-deriving
the schema. Confirm against `data/workstreams/opres-v2/graph.json` before
coding.
