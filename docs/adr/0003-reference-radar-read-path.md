# 3. Reference Radar read path: client-side graph filtering for MVP1

Date: 2026-07-10
Status: Accepted

## Context

The Reference Radar (#26) shows, for the clause a drafter is working on, the
connected external references (peer regulator, act, standard) with their verbatim
passages and a "why this reference matters". External references are modelled as
reference **nodes** (`kind:"reference"`) connected to the drafted clause by
reference↔clause **edges** on the same engine graph (see the engine external-
reference extension). The engine's existing read API already serves the whole
graph (`GET /graph`) and any clause verbatim (`GET /clauses/{n}`); the corpus is
tiny.

## Decision

For **MVP1**, the Radar assembles its view **client-side**: `GET /graph` once,
filter edges where `source == rmit-v2-2026-draft`, `source_clauses` contains the
selected clause, and the target node's `kind == "reference"`; then
`GET /clauses/{target_clause}` for each verbatim passage. `access:"restricted"`
reference nodes (the regulatory handbook) have no ingested passages and render a
locked placeholder — the client never fetches a passage for them.

## Consequences

- No new engine endpoint for MVP1 — the reference extension is limited to
  ingestion + the `kind`/`source_type`/`access`/`preview` node fields and the
  reference↔clause edges.
- The whole graph is already in the client (the workspace loads it), so the Radar
  filters in memory with no extra round-trips beyond the per-passage `GET /clauses`.
- Filtering logic lives in the SPA; if reference volume grows, it moves server-side.

## Alternatives considered

- **A convenience endpoint `GET /clauses/{n}/references`** that returns the
  reference edges anchored on a clause plus their verbatim passages in one call.
  Cleaner client code and cacheable, but adds engine surface for no MVP1 benefit
  on a tiny graph. **Documented as the future path**, not built for MVP1.
- **A separate reference store/service.** Rejected — the brief's whole point is
  "same graph, new node types"; a separate store fragments the model.
