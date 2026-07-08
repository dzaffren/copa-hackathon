# LLM parser + two-agent connection-finder — implementation design

**Ticket:** [#21](https://github.com/dzaffren/copa-hackathon/issues/21) (follow-up to #6)
**Date:** 2026-07-08
**Context:** Ticket #6 (knowledge-graph engine) built the pipeline with the Azure
AI Foundry (Claude) call sites left as `NotImplementedError` stubs — by design,
since #6's acceptance criteria are satisfiable with stubbed model responses and
CI runs without credentials. This design fills those seams so
`python -m engine.build` can generate real `clause-index.json` + `graph.json`,
and `POST /connections/find` can run live.

## Goal

Implement the three deferred Azure AI Foundry (Claude) call sites so the engine
can produce real artifacts and find real connections:

1. `engine.clauses.find_clause_anchors` — the stage-2 clause boundary parser.
2. `engine.connections._finder_turn` — stage-4a candidate proposer.
3. `engine.connections._critic_turn` — stage-4b refute/scope + recall pass.

Plus a copyable `.env.example` and `.env` auto-loading so a filled-in template
"just works".

## Non-goals

- No change to the artifact contract, the `ClauseIndex`/graph shapes, or the
  citation guardrail — those are built and frozen-per-consumer.
- No change to the injectable-seam design in `build.py` / `connections.py`;
  the existing 48 tests must stay green untouched.
- No live-call test in CI — generation is a manual step run with credentials.

## Constraints (from the engine spec)

- The LLM **never produces clause text** — it emits boundaries/anchors
  (`starts_with` snippets) only; `build_clause_index` slices verbatim text.
  For connections, the LLM emits clause **numbers** only; verbatim text is
  re-fetched from the index by number.
- Missing/unfound/ambiguous anchors and unresolvable cited clauses are **loud
  build failures**, never silent corruption (already enforced by
  `build_clause_index` and `build_graph` / the citation validator).
- Determinism of the frozen contract: the parser runs offline; LLM-dependent
  output is committed as artifacts, not re-run at read time.

## Architecture

### New module: `engine/llm.py`

One shared Azure client seam so wiring isn't duplicated across `clauses.py` and
`connections.py`.

- `call_chat(deployment: str, system: str, user: str) -> str` — constructs
  `ChatCompletionsClient` (endpoint/key from `engine.config`, raising a clear
  error if unset), sends `[SystemMessage(system), UserMessage(user)]` via
  `client.complete(...)`, returns `response.choices[0].message.content`.
- `parse_json_response(raw: str) -> list | dict` — strips markdown code fences
  (`json … `), `json.loads`, raises `LLMResponseError` on malformed/empty
  output so a bad turn fails loudly.
- `LLMResponseError(Exception)` — malformed LLM response.

Both helpers are pure/deterministic except `call_chat`'s network call, so the
parsing is fully unit-testable on canned strings with no network.

SDK note: `azure-ai-inference==1.0.0b9` exposes `client.complete(...)` and
`SystemMessage`/`UserMessage`. We request pure JSON via the system prompt and
parse defensively rather than relying on `JsonSchemaFormat` — more portable
across the Anthropic-on-Azure deployments.

### Parser: `find_clause_anchors(markdown, document_id) -> list[dict]`

1. **`_split_sections(markdown) -> list[str]`** — split by top-level numbered
   headings (e.g. `12 Approval for…`, `17 Cloud services`). Bounds per-call
   output size so large docs (RMiT ≈ 762 KB PDF → many clauses) don't risk a
   truncated/incomplete single response.
2. Per section: `call_chat(PARSER_DEPLOYMENT, PARSER_SYSTEM_PROMPT, section)`
   → `_parse_anchor_response(raw)`.
3. **`_parse_anchor_response(raw) -> list[dict]`** — `parse_json_response` then
   validate each object has `clause_number`, `starts_with`, `heading`,
   `parent` (bare numbers; `parent` may be null).
4. Concatenate all sections' anchors in document order; return.

`PARSER_SYSTEM_PROMPT`: few-shot teaching BNM numbering (`17.1`, `17.1(a)`,
`12.3(e)`, `10.50`, `Appendix 10`), instructing the model to return, in
document order, one record per clause with a short **verbatim** `starts_with`
opening phrase — never the full clause text, never character offsets.

### Finder: `_finder_turn(doc_a_id, doc_b_id, clause_index) -> list[dict]`

1. **`_clauses_for_document(clause_index, document_id)`** — pull every primary
   entry whose `document_id` matches; format as `{clause_number}: {text}`
   blocks (a `_format_clause_context` helper).
2. `call_chat(FINDER_CRITIC_DEPLOYMENT, FINDER_SYSTEM_PROMPT, both_blocks)` →
   `parse_json_response`.
3. Return raw candidate dicts: `{summary, source_clauses[], target_clauses[],
scope_note?}` — the exact shape `find_connections` already consumes.

`FINDER_SYSTEM_PROMPT`: propose cross-policy connections; cite exact clause
numbers **from the provided lists only**; never invent a clause number.

### Critic: `_critic_turn(doc_a_id, doc_b_id, clause_index, candidates) -> list[dict]`

Same clause context as the finder **plus** the finder's candidates serialised
into the user message. `CRITIC_SYSTEM_PROMPT` does two jobs: (i) refute/scope
weak candidates (add `scope_note`, e.g. the affiliate-exemption scoping), and
(ii) surface missed connections (recall). Returns the scoped set **plus** newly
found ones, same raw shape.

The clause **text** in a finder/critic candidate is never trusted:
`find_connections` re-fetches verbatim text by number and drops any candidate
citing an unresolvable clause (the existing, tested guardrail). The turns emit
numbers; correctness is code-enforced downstream.

### Config / `.env`

- `.env.example` (tracked, no secrets) with the four vars:
  `AZURE_FOUNDRY_ENDPOINT`, `AZURE_FOUNDRY_API_KEY`,
  `AZURE_FOUNDRY_PARSER_DEPLOYMENT` (`claude-sonnet-5`),
  `AZURE_FOUNDRY_FINDER_CRITIC_DEPLOYMENT` (`claude-opus-4-8`).
- `engine/config.py` loads `.env` via `python-dotenv` (new dep) before reading
  env, so a copied+filled `.env` works with no manual `export`. `.env` stays
  git-ignored.

## Error handling

| Condition                              | Behaviour                                                                                  |
| -------------------------------------- | ------------------------------------------------------------------------------------------ |
| Endpoint/key unset                     | Clear `RuntimeError` (parser) / `ConnectionFindError` (finder/critic) — unchanged messages |
| Malformed/empty LLM JSON               | `LLMResponseError` — loud, build fails                                                     |
| Anchor `starts_with` unfound/ambiguous | Existing `ClauseAnchorNotFoundError` / `ClauseAnchorAmbiguousError`                        |
| Emitted clause set incomplete          | Existing `ClauseCompletenessError` (when `expected_clauses` supplied)                      |
| Candidate cites unresolvable clause    | Existing citation validator → `unsupported`, never invented                                |

## Testing

- **Unit, no network:** `_split_sections`, `parse_json_response` (fenced,
  bare array, malformed→raises, empty→raises), `_parse_anchor_response`
  (valid, missing-key→raises), finder/critic response parsing on canned
  strings.
- **Regression:** the existing 48 tests stay green — the injectable
  `finder_fn`/`critic_fn`/`find_anchors_fn` seams mean their stubs are
  untouched.
- **Live generation:** manual — `python -m engine.build` with credentials set.
  Not in CI (no credentials there).

## Known first-run gotcha (documented, not fixed blind)

`engine/config.py::CURATED_SEED_EDGES` carries **placeholder** clause anchors
on the pairs not validated by the blind test — `BCM 5.1`, `Customer Info 8.1`,
`Operational Resilience 6.11`, and the `RMiT 17.1`→BCM/Customer-Info anchors.
`build_graph` hard-fails if any edge clause doesn't resolve in the parsed
index. So the **first real generation will likely fail on those edges** until
they are corrected to real parsed clause numbers. This is the guardrail working
as designed. Correcting them requires the real parsed output, so it is a
follow-up step after the first successful parse — not part of this change.

## Files

- `engine/llm.py` — new: `call_chat`, `parse_json_response`, `LLMResponseError`.
- `engine/clauses.py` — implement `find_clause_anchors` + `_split_sections`,
  `_parse_anchor_response`, `PARSER_SYSTEM_PROMPT`.
- `engine/connections.py` — implement `_finder_turn` / `_critic_turn` +
  `_format_clause_context`, prompts; route both through `engine/llm.py`.
- `engine/config.py` — load `.env` via `python-dotenv`.
- `.env.example` — new, tracked template.
- `pyproject.toml` / `uv.lock` — add `python-dotenv`.
- Tests: `engine/tests/test_llm.py` (new), additions to
  `test_clauses.py` / `test_connections.py` for the new parsing helpers.
