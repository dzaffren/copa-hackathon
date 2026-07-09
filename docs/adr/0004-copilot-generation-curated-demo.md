# 4. Drafting copilot generation: curated demo-safe fixtures for MVP1

Date: 2026-07-10
Status: Accepted

## Context

The drafting copilot (#9) produces generative prose: redraft wording, "grill"
challenges, and plain-language answers about the rulebook and the references. The
engine's model access is **build-time only** — the served read API has no model,
and #8's `POST /connections/find` is the single place the product runs the model
live on stage. For MVP1 (a 3 Aug 2026 hackathon demo) the copilot's generative
text needs a source that is reliable on stage and keeps the verbatim-citation
guardrail real.

## Decision

For **MVP1**, the copilot's generative prose comes from **curated demo-safe
fixtures** (`web/src/fixtures/copilot-responses.json`), keyed by mode + finding.
Crucially, **every clause a response quotes is fetched live from
`GET /clauses/{n}`** at answer time — so the verbatim-citation guardrail is real
(an answer with no supporting clause returns "No clause in the rulebook supports
this"), not baked into the fixture. Grounded web-search results likewise come from
a curated allowlist fixture (`web/src/fixtures/trend-allowlist.json`), each result
cited and stored so a finding stays reproducible.

The **production** path is a thin server proxy to the Azure model behind the same
copilot interface, with the identical citation-validation guardrail applied to the
model's output before it reaches the drafter.

## Consequences

- The demo is deterministic — no live-model latency or flakiness during the pitch,
  while #8's single live-AI moment still proves the model is real.
- The guardrail is genuinely enforced (clauses fetched live, unsupported answers
  say so), not simulated — the property judges care about survives the fixture.
- Swapping to a live proxy later is a change behind the copilot service module.

## Alternatives considered

- **Live model call from the copilot now.** Most impressive, but the read API has
  no model access, it needs credentials, and on-stage latency/flakiness is a real
  risk for a timed demo — rejected for MVP1, kept as production.
- **Fully static responses (clauses baked into the fixture).** Simplest, but loses
  the live `GET /clauses` guardrail proof — an invented citation could ship
  unnoticed. Rejected.
