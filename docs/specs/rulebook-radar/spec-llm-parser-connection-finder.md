# LLM parser + two-agent connection-finder — implementation design

**Ticket:** [#21](https://github.com/dzaffren/copa-hackathon/issues/21) (follow-up to #6)
**Date:** 2026-07-08
**Status:** In progress — single-doc build works; full 6-doc build not yet
complete. **The plan sections below are the original design; several parts are
stale. Read "Implementation status" at the bottom first — it is the source of
truth for the current state and next steps.**
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

---

## Implementation status (2026-07-08, end of session)

The plan above is the original design; **reality diverged** as we ran the parser
against the real BNM PDFs. This section is the source of truth for the current
state — read it first when resuming.

### What was built & works

- **`engine/llm.py`** — shared LLM seam + `parse_json_response` + `LLMResponseError`.
- **Parser (`find_clause_anchors`)**, **finder/critic turns**, **`.env` loading**
  (`python-dotenv`), **`.env.example`** — all implemented.
- **A single document (`--docs outsourcing-v1-2019`) builds end-to-end into a
  clean, verbatim `clause-index.json`** — 173 clauses, 0 garbled, 0 marker
  leakage, load-bearing `Outsourcing 12.1` byte-perfect, ~2–3% of anchors
  dropped (non-load-bearing boilerplate, logged).
- **96 tests pass, ruff clean, mypy = 4 (accepted third-party-stub baseline).**

### Key deviations from the plan above (IMPORTANT — the plan is stale here)

1. **Not `azure-ai-inference` — the `anthropic` SDK.** Claude on Foundry speaks
   the **Anthropic Messages API**, not the generic chat-completions API (which
   returns `api_not_supported`). `call_chat` uses
   `anthropic.AnthropicFoundry(api_key, base_url=…/anthropic)` +
   `client.messages.create(system=…, messages=[{user}], max_tokens=…)`. **Base
   URL must end in `/anthropic`.**
2. **No assistant-prefill.** Prefill 400s on the Claude 4.6+ family (incl. the
   deployed `claude-opus-4-8` / `claude-sonnet-5`). JSON is forced by prompt +
   defensive parsing only.
3. **`parse_json_response` is much more tolerant than planned** — handles: code
   fences, JSON Lines (object-per-line), a junk preamble object before the real
   array + trailing prose (salvages top-level arrays via `raw_decode`).
4. **Chunking is clause-aware + size-bounded, not `_split_sections`.**
   `_split_chunks` cuts at top-level clause boundaries (`_CLAUSE_START_RE` =
   `N.M` or `Appendix N` only — bare `N Capital` lines are footnotes, NOT
   boundaries), packs whole clauses up to `_MAX_CHUNK_CHARS` (6000), and
   sub-splits any oversized block via `_split_paragraphs` (hard char-split
   fallback) so no LLM call overflows its output limit.
5. **Retry on non-JSON** — `_parse_chunk_with_retry` (parser) and
   `_call_candidates_with_retry` (finder/critic) re-ask up to 3× before failing.
6. **Unresolvable anchors are DROPPED with a warning, NOT crashed on.** Empty /
   not-found / still-ambiguous `starts_with` → logged + counted per document,
   build continues. `ClauseCompletenessError` (when `expected_clauses` is
   supplied) is the backstop for load-bearing clauses. This replaced the "loud
   build failure" behaviour in the Error-handling table above.
7. **Anchor location is whitespace-insensitive** (MarkItDown emits doubled
   spaces; the model normalises them) and **disambiguates recurring phrases by
   the clause's deepest label** (`(i)` for `9.6(c)(i)`, `(c)` for `8.4(c)`).
8. **Trailing BNM `S`/`G` (Standard/Guidance) marker is trimmed** from both a
   clause's `text` and the composed `full_text`.

### THE ROOT-CAUSE FIX: Azure Document Intelligence backend

Default MarkItDown **scrambles reading order** on BNM's multi-column PDFs
(stranded list labels, lost clause bodies, page headers mid-clause) — this was
the source of most parser failures. **`engine/ingest.py` now routes PDFs through
Azure AI Document Intelligence (`prebuilt-layout`)** when
`AZURE_DOCINTEL_ENDPOINT` + `AZURE_DOCINTEL_API_KEY` are set (unset → default
extractor, no CI/Azure dependency). Output stays verbatim source text →
citation guarantee intact.

- **Gotcha (fixed):** MarkItDown hardcodes an old preview api-version that GA DI
  resources reject with `404` and then **silently swallows**, falling back to
  the default extractor. `AZURE_DOCINTEL_API_VERSION` (default `2024-11-30`) is
  passed through — **required, not optional**.
- Deps added: `markitdown[az-doc-intel]`, `anthropic`, `python-dotenv`.

### Env vars now required for a live build (all in `.env`, git-ignored)

```
AZURE_FOUNDRY_ENDPOINT=https://<resource>.services.ai.azure.com/anthropic   # MUST end /anthropic
AZURE_FOUNDRY_API_KEY=…
AZURE_FOUNDRY_PARSER_DEPLOYMENT=claude-sonnet-5
AZURE_FOUNDRY_FINDER_CRITIC_DEPLOYMENT=claude-opus-4-8
AZURE_DOCINTEL_ENDPOINT=https://<resource>.cognitiveservices.azure.com/
AZURE_DOCINTEL_API_KEY=…
AZURE_DOCINTEL_API_VERSION=2024-11-30
```

### WHERE WE STOPPED — next steps, in order

1. **Full 6-doc build (`python -m engine.build`, no `--docs`) has NOT completed.**
   Single-doc works; the last failure was RMiT's oversized-chunk truncation,
   now fixed (`f94288f`). Re-run the full build and see how far it gets.
2. **Expected next failure — graph build on phantom curated anchors.**
   `CURATED_SEED_EDGES` in `engine/config.py` cites clauses that don't exist in
   the real parsed corpus — confirmed **`Operational Resilience 6.11` is NOT in
   the OpRes Discussion Paper at all** (that doc uses single-digit `1.1…`
   numbering; no clause 6.11). `BCM 5.1` / `Customer Info 8.1` are also
   placeholders. `build_graph` will fail with `GraphBuildError` naming the
   unresolvable clause. **Fix = correct the config's clause anchors to real
   parsed clause numbers (or drop/relabel those edges)** — a config-data fix,
   not a parser fix.
3. **Non-determinism** — the model returns a slightly different anchor set each
   run (anchor counts drift 172–217; different clauses drop each time). For a
   **stable, frozen artifact** the plan (per #6 spec) is to generate once and
   **commit `clause-index.json` / `graph.json` as fixtures**, not regenerate
   live. Decide this before relying on artifact stability downstream.
4. **Load-bearing clause audit** — once the full build completes, verify the
   demo-critical clauses survived and are verbatim: Outsourcing 12.1 (✅ so far),
   RMiT 17.1/17.2/10.50 (note RMiT v2 conflict text comes from the **mock draft**
   `data/mock/`, not the PDF), the OpRes "register of critical services" clause
   (its real number, since 6.11 is phantom).
5. **Extraction quality is uneven per doc** (stranded-label diagnostic):
   recovery/bcm clean, custinfo near-clean, opres/rmit moderate, outsourcing
   worst. DI should improve all; re-measure if a doc parses poorly.

### Branch / tracking

Branch `feature/21-live-azure-llm-calls` off `main` (which has #6 merged). Many
commits this session (`fix(llm)`, `fix(clauses)`, `feat(ingest)` DI backend,
etc.), all local — **not yet pushed, no PR opened**. Ticket #21. `.env` is
git-ignored and populated locally with working DI + Foundry creds.
