# `_cross` — linkages that span two workstreams

Every other directory under `data/workstreams/` is one workstream. This one is
not: it holds edges whose two endpoints live in **different** workstreams, and
the findings on them. `Operational Resilience` and `Open Finance` are drafted by
different teams on different timelines; a linkage between them belongs to
neither `graph.json`, so it lives here.

It has **no `workstream.json`**, and that is deliberate — `list_workstreams()`
skips any directory without one, so `_cross` never appears in the sidebar as a
workstream the drafter can open. It is a store, not a workstream.

Its `graph.json` follows the ordinary node/edge shape, with two additions:
`workstream_id` on each node and `source_workstream_id` / `target_workstream_id`
on each edge, naming where each endpoint really lives. That shape is what lets
the **existing** review route serve these findings unchanged — the drafter reads,
accepts, and dismisses a cross-workstream linkage on the same screen as any
other, at `/workstreams/_cross/edges/{edge_id}/review`.

## The findings are not fixtures

`findings/x-open_finance_ed--opres_dp_2025.json` is a projection of a **real**
finder+critic run (2026-07-11, `claude-opus-4-8`) recorded at
`data/artifacts/connection-trace-opres-v1-2025-draft__open-finance-v1-2025-ed.json`:
12 linkages between two concurrent BNM workstreams, found with **zero curated
seed edges** between them. This is the experiment that retired the project's
riskiest assumption — see `docs/discovery/workstream-brain/brief.md`.

Regenerate with:

```
PYTHONPATH=. python scripts/project_cross_workstream_findings.py
```

The projection resolves the trace's clause numbers to verbatim text **once**, at
build time, and embeds the quotes. That is the point: the trace itself stores
numbers only, so its citations were silently un-cited when a rebuild narrowed the
clause index (#34 — the trace resolved 0 of 48 clauses until it was recovered).
Embedding the text means narrowing the index can no longer un-cite the demo.

One clause — `Operational Resilience 3.3(e)` — does not resolve offline and
renders as "No matching clause found" rather than being dropped or invented.
That is the product rule working, in public, on the demo's own data.
