# Widen the linkage taxonomy in the knowledge-graph engine

**Epic:** [Workstream Brain MVP1 — Overview](spec.md)
**Ticket:** TBD
**Type:** Technical — Engine

The knowledge-graph engine today emits findings labelled with a three-way vocabulary (Conflict / Duplication / Gap) that is too narrow to describe the range of relationships a workstream member cares about. This work replaces that vocabulary with a five-label semantic taxonomy plus an optional sentiment tag on one of the labels, keeps the verbatim-citation guarantee intact, and preserves the ability to re-run the retired experiment trace under the new labels. Every user-facing screen in the epic consumes these labels, so this is the first story to land.

## Motivation

Cross-workstream drift is invisible today because senior policymakers carry linkage knowledge in their heads. The engine already discovers linkages between clause pairs and validates their citations verbatim — but the labels it applies to those linkages cannot express the distinctions drafters actually make on the job. A drafter needs to know whether the two documents agree, disagree on the same axis, are outright incompatible, or are simply silent on each other. The current three labels collapse all of these into "conflict" or "gap", which produces false alarms on legitimate policy divergence and hides genuinely important asymmetries.

**Current state:** The engine emits linkages using a Conflict / Duplication / Gap vocabulary. It cannot distinguish deliberate policy divergence (a BNM PD tightening a peer-regulator threshold) from an incompatibility (two documents cannot both be followed), and it cannot distinguish coverage asymmetry direction (they cover something we do not vs we cover something they do not). Sentiment on divergence findings — tighten / loosen / neutral — is not captured at all.

**Desired state:** Every finding the engine emits carries exactly one of five semantic labels: `aligns-with`, `differs-on`, `conflicts-with`, `silent-on`, or `goes-beyond`. Findings labelled `differs-on` may additionally carry a sentiment tag of `tighten`, `loosen`, or `neutral`. The direction convention is fixed: the first document in a pair is treated as "our" side (the workstream's own document) and the second as "their" side (the anchor). The retired experiment trace can be re-processed under the new taxonomy without losing any of the twelve supported linkages it originally produced.

**Trigger:** The Workstream Brain MVP1 epic depends on the widened taxonomy — every downstream screen (workstream graph edge-detail, review linkages, task pairwise comparison, drafting workspace linkage tabs) renders semantic labels as label pills and filters on them. Building any downstream screen against the old three-way vocabulary would force a rework once this story lands, so this story ships first.

## Scope

- **In scope:**
  - Replace the Conflict / Duplication / Gap emitted label with one of the five new semantic labels on every finding the finder→critic loop produces.
  - Add an optional sentiment tag (`tighten` / `loosen` / `neutral`) that attaches only to findings labelled `differs-on`.
  - Fix the direction convention: the first document in a pair is "we/ours"; the second is "they/theirs". Coverage-asymmetry labels (`silent-on`, `goes-beyond`) flip when the pair is swapped.
  - Preserve the verbatim-citation guarantee: findings whose cited clauses cannot be resolved to real clauses become "No matching clause found" and are not emitted as labelled findings.
  - Preserve the connection trace written to disk so it records the new label and sentiment fields alongside the existing citation payloads.
  - Confirm the retired experiment trace can be re-processed end-to-end under the new taxonomy without losing any of its twelve supported linkages.
- **Out of scope:**
  - Any user-facing screen work. Rendering label pills, sentiment badges, and filters is the responsibility of the workstream-graph, review-linkages, task, and drafting-workspace stories.
  - Ontology-based concept extraction and cross-workstream concept overlap. That is a separate pipeline outside this epic.
  - Correction feedback loops (accepting or dismissing a finding feeding back into future runs). Deferred per the epic non-goals.
  - Live LLM calls at demo time. The engine's demo behaviour replays the retired trace; live calls stay behind the existing seam.
  - Changing the finder or critic prompting strategy beyond what is required to emit the new labels correctly.

## Goals

- Every finding the engine produces after this story carries exactly one of the five semantic labels and, where applicable, a sentiment tag.
- The five labels are mutually exclusive and collectively exhaustive over the space of linkages the engine can produce. A finding is never emitted with two labels; it is never emitted with none.
- The retired experiment trace re-processes under the new taxonomy with all twelve supported linkages preserved and zero fabricated citations introduced.
- Downstream screens can filter, group, and render findings by label and sentiment without further engine changes.

## Non-Goals

- Retraining or fine-tuning the underlying language model.
- Migrating historical traces produced by unrelated experiments — only the retired OpRes × Open Finance trace is in scope.
- Emitting labels for structural edges on the workstream graph. Structural edges (`supersedes`, `references`, `contributes-to`, `parallel-to`) are declared by the user at node-creation time and are unaffected by this work.

## Success Criteria

- Running the engine on any supported document pair produces findings whose labels are drawn only from the five-value set, with sentiment tags appearing only on `differs-on` findings.
- Re-processing the retired experiment trace preserves all twelve originally supported linkages and introduces zero fabricated citations.
- Swapping the two documents in a pair correctly flips coverage-asymmetry labels: what was `silent-on` becomes `goes-beyond` and vice versa; `aligns-with`, `differs-on`, and `conflicts-with` remain the same label regardless of direction.
- Every finding labelled `differs-on` where one side clearly tightens or loosens the other carries the corresponding sentiment tag; findings where the divergence is orthogonal (neither tighter nor looser) carry `neutral` or no sentiment.
- Findings whose cited clauses cannot be resolved never reach a downstream screen with a semantic label. They surface as unsupported with the standard "No matching clause found" message.

## Business Examples

The examples below are drawn from the workstream corpus used for the hackathon demo. They anchor the taxonomy in real content the engine already processes.

**Example 1 — `aligns-with` (BCBS mother-doc adoption).** Operational Resilience PD v0.3 §4.4 (dependency mapping requirement) versus BCBS Operational Resilience 2021 Principle 7 (identify and manage third-party dependencies). Both documents speak to the same axis — mapping and managing external dependencies critical to operational resilience — and BNM's clause operationalises the BCBS principle without narrowing or widening it. The engine emits `aligns-with`.

**Example 2 — `differs-on` with `tighten` sentiment (peer-regulator comparison).** Operational Resilience PD v0.3 §5.3 (annual scenario testing minimum) versus HKMA Supervisory Policy Manual OR-2 §5.2 (biennial scenario testing minimum). Same axis — scenario testing cadence — different position on the threshold. BNM sets a stricter minimum than HKMA. The engine emits `differs-on` with sentiment `tighten`.

**Example 3 — `conflicts-with` (version drift catch).** Operational Resilience PD v0.3 §7.1 (references RMiT PD dated 1 June 2023) versus the reissued RMiT PD dated 28 November 2025. Applying both as written is incompatible because the cited RMiT edition no longer exists in force. The engine emits `conflicts-with`. This is the version-drift exhibit the discovery brief committed to landing on stage.

**Example 4 — `goes-beyond` (coverage asymmetry, our side).** Operational Resilience PD v0.3 §6.3 (requirement to appoint a single accountable officer for operational resilience) versus the RMiT PD (no equivalent single-officer requirement). The two documents both address governance, but only BNM's OpRes draft covers this specific requirement. With the direction convention set to OpRes as "we/ours", the engine emits `goes-beyond`. Swapping the pair — RMiT as "we/ours" — would flip the label to `silent-on`.

## Acceptance Criteria

### Scenario: Engine emits a five-label semantic taxonomy on every finding

```gherkin
Given the engine has completed a finder-then-critic run on a supported document pair
When the engine writes the run's findings to the connection trace
Then every finding carries exactly one semantic label
  And the label is drawn from the set aligns-with, differs-on, conflicts-with, silent-on, goes-beyond
  And no finding carries the retired labels Conflict, Duplication, or Gap
  And no finding carries two labels or no label
```

### Scenario: Same-axis agreement produces aligns-with

```gherkin
Given the pair is Operational Resilience PD v0.3 as our side and BCBS Operational Resilience 2021 as their side
  And OpRes PD section 4.4 and BCBS Principle 7 both address managing external dependencies critical to operational resilience
  And the two clauses agree on the axis without narrowing or widening
When the engine produces a finding for this clause pair
Then the finding is labelled aligns-with
  And the finding carries no sentiment tag
  And both cited clauses are quoted verbatim from the clause index
```

### Scenario: Same-axis deliberate divergence carries differs-on with a tighten sentiment

```gherkin
Given the pair is Operational Resilience PD v0.3 as our side and HKMA Supervisory Policy Manual OR-2 as their side
  And OpRes PD section 5.3 requires scenario testing at least annually
  And HKMA SPM OR-2 section 5.2 requires scenario testing at least once every two years
When the engine produces a finding for this clause pair
Then the finding is labelled differs-on
  And the finding carries the sentiment tag tighten
  And both cited clauses are quoted verbatim from the clause index
```

### Scenario: Same-axis deliberate divergence carries differs-on with a loosen sentiment

```gherkin
Given the pair is a BNM draft that permits a wider set of outsourcing arrangements than a peer regulator does on the same axis
  And the peer regulator's clause imposes a narrower permission
When the engine produces a finding for this clause pair
Then the finding is labelled differs-on
  And the finding carries the sentiment tag loosen
  And both cited clauses are quoted verbatim from the clause index
```

### Scenario: Same-axis orthogonal divergence carries differs-on with a neutral sentiment or no sentiment

```gherkin
Given the pair is two documents that speak to the same axis but position differently in a way that is neither tighter nor looser
When the engine produces a finding for this clause pair
Then the finding is labelled differs-on
  And the finding carries either the sentiment tag neutral or no sentiment tag
  And no other label carries a sentiment tag
```

### Scenario: Incompatible requirements produce conflicts-with

```gherkin
Given the pair is Operational Resilience PD v0.3 as our side and RMiT PD dated 28 November 2025 as their side
  And OpRes PD section 7.1 references the RMiT PD dated 1 June 2023 as still in force
  And the RMiT PD dated 28 November 2025 supersedes the 1 June 2023 edition
  And applying both documents as written is incompatible
When the engine produces a finding for this clause pair
Then the finding is labelled conflicts-with
  And the finding carries no sentiment tag
  And both cited clauses are quoted verbatim from the clause index
```

### Scenario: Coverage asymmetry — their side covers, our side does not — produces silent-on

```gherkin
Given the pair sets our side as the document that does not address a specific requirement
  And their side is the document that does address that requirement
When the engine produces a finding for this coverage gap
Then the finding is labelled silent-on
  And the finding carries no sentiment tag
  And the cited clause on their side is quoted verbatim from the clause index
```

### Scenario: Coverage asymmetry — our side covers, their side does not — produces goes-beyond

```gherkin
Given the pair is Operational Resilience PD v0.3 as our side and RMiT PD as their side
  And OpRes PD section 6.3 requires appointing a single accountable officer for operational resilience
  And the RMiT PD does not contain an equivalent single-officer requirement
When the engine produces a finding for this coverage asymmetry
Then the finding is labelled goes-beyond
  And the finding carries no sentiment tag
  And the cited clause on our side is quoted verbatim from the clause index
```

### Scenario: Swapping the document direction flips coverage-asymmetry labels

```gherkin
Given the engine has produced a finding labelled silent-on for a document pair with side A as our side and side B as their side
When the same pair is re-run with side B as our side and side A as their side
Then the equivalent finding is labelled goes-beyond
  And the underlying cited clauses are unchanged
  And no finding originally labelled aligns-with, differs-on, or conflicts-with changes its label as a result of the swap
```

### Scenario: Sentiment tags never attach to labels other than differs-on

```gherkin
Given the engine has produced a batch of findings across all five labels
When the connection trace is inspected
Then only findings labelled differs-on carry a sentiment tag
  And every sentiment tag drawn from tighten, loosen, or neutral appears only on differs-on findings
  And findings labelled aligns-with, conflicts-with, silent-on, or goes-beyond carry no sentiment tag
```

### Scenario: Sentiment tag on differs-on applies to internal-versus-internal pairs

```gherkin
Given the pair is two already-published BNM policy documents
  And both documents speak to the same axis but position differently on a threshold
When the engine produces a finding for this clause pair
Then the finding is labelled differs-on
  And the finding carries the applicable sentiment tag from tighten, loosen, or neutral
  And the internal-versus-internal nature of the pair does not suppress the sentiment tag
```

### Scenario: A finding whose cited clauses cannot be resolved is not emitted with a semantic label

```gherkin
Given the finder proposes a candidate finding that cites a clause number the clause index cannot resolve to a real clause
When the critic and citation validator process the candidate
Then the candidate is not emitted as a labelled finding
  And it appears in the unsupported list with the message "No matching clause found"
  And no semantic label or sentiment tag is attached to the unsupported entry
  And no fabricated clause text is written to the connection trace
```

### Scenario: Re-processing the retired experiment trace preserves all twelve supported linkages

```gherkin
Given the retired experiment trace for the Operational Resilience v0.3 draft versus the Open Finance 2025 Exposure Draft pair
  And the trace originally contained twelve supported linkages and zero unsupported linkages under the old three-way vocabulary
When the trace is re-processed under the new five-label taxonomy
Then all twelve linkages remain present as supported findings
  And each of the twelve carries exactly one of the five new semantic labels
  And any differs-on finding among the twelve carries the applicable sentiment tag
  And zero fabricated citations are introduced
  And zero originally-supported linkages are dropped from the trace
```

### Scenario: The five labels partition the space of findings the engine emits

```gherkin
Given the engine has completed a finder-then-critic run producing a batch of findings
When each finding is inspected for its label
Then every finding falls into exactly one of aligns-with, differs-on, conflicts-with, silent-on, and goes-beyond
  And aligns-with, differs-on, and conflicts-with together cover every finding where both sides speak to the same axis
  And silent-on and goes-beyond together cover every finding of coverage asymmetry
  And no finding is left uncategorised
```

### Scenario: Connection trace records the new label and sentiment fields

```gherkin
Given the engine has completed a finder-then-critic run and written the results to a connection trace
When the connection trace is read back for a downstream screen
Then every supported finding in the trace carries its semantic label
  And every differs-on finding carries its sentiment tag where one applies
  And the trace remains readable end-to-end without loss of the verbatim clause citations
```

## Constraints

- **Backwards compatibility:** The old three-way vocabulary (Conflict / Duplication / Gap) is retired and no longer emitted. No downstream screen in this epic depends on the old labels, so a clean cutover is acceptable. Historical traces outside the retired experiment trace are out of scope.
- **Verbatim citations:** Non-negotiable. Every finding emitted with a semantic label must resolve to a real clause in the clause index for both cited sides. This is a product rule from the codebase, not a preference.
- **Determinism at demo time:** The demo replays the retired experiment trace rather than making live LLM calls. The taxonomy change must not alter the ability to replay the trace.
- **Rollback:** Not required to be reversible in production terms — no production system exists. If the taxonomy is found to be inadequate during build week, the fallback is to iterate the labels, not to revert.

## Dependencies

- **Retired experiment trace** for the Operational Resilience v0.3 draft versus Open Finance 2025 Exposure Draft pair — the twelve-linkage baseline that must survive re-processing under the new taxonomy.
- **Existing clause index** — every cited clause must resolve here; the verbatim guarantee depends on it.
- **Existing finder→critic loop and citation validator** — the seams stay in place; only the label vocabulary emitted through them changes.

## Open Questions

- [x] ~~Should sentiment apply to labels other than `differs-on`?~~ — **Resolved:** No. Sentiment applies only to `differs-on`. Applying tighten/loosen to `aligns-with` or `conflicts-with` collapses distinctions the labels are there to preserve.
- [x] ~~Should `differs-on` always carry a sentiment tag?~~ — **Resolved:** No. Sentiment is optional. Orthogonal divergences carry either `neutral` or no sentiment tag; a downstream screen that requires a value can default to `neutral`.
- [x] ~~Should the direction convention be configurable per run?~~ — **Resolved:** No. The convention is fixed: the first document in the pair is "we/ours", the second is "they/theirs". Callers that want the opposite orientation swap the arguments and accept the flipped coverage-asymmetry labels.
- [ ] Whether a `differs-on` finding can additionally be flagged as a benchmarking-relevant divergence when the paired anchor is a peer regulator — **Deferred (non-blocking):** downstream screens can compute this from the paired document's node type; the engine does not need to encode register on the finding itself.

---

## Solution Design

The taxonomy widening lands entirely inside `engine/connections.py` plus the trace writer and a single one-off backfill script. No new modules, no new dependencies, no changes to the clause index, the citation validator's clause-resolution logic, or the network seam. The finder→critic loop's shape is preserved: only the object schema the two turns emit — and therefore what `_validate_candidates` accepts and what `_write_trace` records — grows two fields.

Concretely:

- Widen the `Connection` TypedDict in `engine/connections.py` (lines 57-66) to add a required `label: Literal["aligns-with", "differs-on", "conflicts-with", "silent-on", "goes-beyond"]` field and an optional `sentiment: Optional[Literal["tighten", "loosen", "neutral"]]` field.
- Widen the `UnsupportedConnection` TypedDict (lines 68-75) with the same two fields so that if a candidate proposes a label but its citation cannot be resolved, the trace still records what the model attempted for auditability. The `label` field on `UnsupportedConnection` may be `None` when the candidate never proposed one.
- Update `FINDER_SYSTEM_PROMPT` and `CRITIC_SYSTEM_PROMPT` (lines 293-331) so the candidate JSON schema they emit contains `label` (required, one of five values) and `sentiment` (optional, one of three values). The prompts must state the direction convention (document A is "we/ours", document B is "they/theirs") and the sentiment-only-on-differs-on rule.
- Extend `_parse_candidate_list` (lines 353-379) to enforce the new schema: raise `LLMResponseError` if a candidate is missing `label`, if `label` is outside the five-value set, if `sentiment` is present on any label other than `differs-on`, or if `sentiment` is present with a value outside the three-value set.
- Extend `_validate_candidates` (lines 177-237) to carry the parsed `label` and `sentiment` through to the built `Connection` (or `UnsupportedConnection`) record. The clause-resolution branch is untouched — it stays the verbatim-citation guardrail.
- Extend `_write_trace` (lines 260-290) so each entry in the `validation` list records the candidate's `label` and `sentiment` alongside the existing `cited_clauses` and `supported` fields.
- Bump `pyproject.toml` `requires-python` to `>=3.12` to license the `Literal[...]` and `Optional[Literal[...]]` annotations at import time without a `__future__` dance.

### Changes

- `engine/connections.py` — widen the two TypedDicts, rewrite both system prompts, extend `_parse_candidate_list`, `_validate_candidates`, and `_write_trace` to carry `label` + `sentiment`. Do NOT touch `_cite` or the clause-lookup logic inside `_validate_candidates`.
- `engine/tests/test_connections.py` — add unit tests for the new label/sentiment enforcement and direction-flip behaviour, using stubbed `finder_fn` and `critic_fn`.
- `pyproject.toml` — bump `requires-python = ">=3.12"`.
- `scripts/backfill_taxonomy.py` — new one-off script that maps the retired trace's twelve findings from the old three-way vocabulary to the five-label taxonomy via deterministic string matching. No LLM calls.
- `data/artifacts/connection-trace-opres-v1-2025-draft__open-finance-v1-2025-ed.json` — rewritten in place by the backfill script so the demo backstop matches the new schema.

### Data Model

**Widened `Connection` (supported finding):**

| Field            | Type                                                                                 | Constraints                                                                    | Description                                   |
| ---------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ | --------------------------------------------- |
| `summary`        | `str`                                                                                | Required, non-empty                                                            | One-sentence description of the finding       |
| `source_clauses` | `list[ClauseCitation]`                                                               | Required, non-empty; every citation resolves in the clause index               | Verbatim citations on document A (our side)   |
| `target_clauses` | `list[ClauseCitation]`                                                               | Required, non-empty; every citation resolves in the clause index               | Verbatim citations on document B (their side) |
| `scope_note`     | `Optional[str]`                                                                      | Optional                                                                       | Critic-added caveat or exemption note         |
| `supported`      | `bool`                                                                               | Always `True` on `Connection`                                                  | Verbatim-guarantee flag                       |
| `label`          | `Literal["aligns-with", "differs-on", "conflicts-with", "silent-on", "goes-beyond"]` | Required                                                                       | Semantic label (one of five)                  |
| `sentiment`      | `Optional[Literal["tighten", "loosen", "neutral"]]`                                  | Present only when `label == "differs-on"`; must be `None` for all other labels | Sentiment tag on divergence findings          |

**Widened `UnsupportedConnection`:** identical to today plus `label: Optional[str]` and `sentiment: Optional[str]` so the audit trail records what the model attempted before the citation validator dropped it.

**Trace file schema (`connection-trace-{pair}.json`):** the `validation` list entries gain `label` and `sentiment` fields. The `finder_output` and `critic_output` arrays record whatever raw candidates the two agents returned, which now include `label` and `sentiment` in their objects.

**Sample JSON — `aligns-with` (no sentiment):**

```json
{
  "summary": "OpRes PD's dependency-mapping requirement operationalises the BCBS principle on identifying and managing third-party dependencies without narrowing or widening the axis.",
  "source_clauses": [
    {
      "clause_number": "Operational Resilience 4.4",
      "text": "A financial institution shall map its dependencies on external service providers that support critical operations..."
    }
  ],
  "target_clauses": [
    {
      "clause_number": "BCBS OpRes Principle 7",
      "text": "Banks should manage their dependencies on relationships, including but not limited to those of third parties or intra-group entities..."
    }
  ],
  "scope_note": null,
  "supported": true,
  "label": "aligns-with",
  "sentiment": null
}
```

**Sample JSON — `differs-on` with `tighten` sentiment:**

```json
{
  "summary": "OpRes PD sets a stricter scenario-testing cadence than HKMA on the same axis: annual versus biennial.",
  "source_clauses": [
    {
      "clause_number": "Operational Resilience 5.3",
      "text": "A financial institution shall conduct scenario testing of its operational resilience arrangements at least annually."
    }
  ],
  "target_clauses": [
    {
      "clause_number": "HKMA SPM OR-2 5.2",
      "text": "An authorized institution should conduct scenario testing at least once every two years."
    }
  ],
  "scope_note": null,
  "supported": true,
  "label": "differs-on",
  "sentiment": "tighten"
}
```

**Sample JSON — `silent-on` (our side does not cover, their side does):**

```json
{
  "summary": "The Open Finance ED requires periodic independent review of API security controls; the OpRes DP does not address independent review of API security specifically.",
  "source_clauses": [],
  "target_clauses": [
    {
      "clause_number": "Open Finance 12.5",
      "text": "The financial institution shall commission an independent review of its API security controls..."
    }
  ],
  "scope_note": null,
  "supported": true,
  "label": "silent-on",
  "sentiment": null
}
```

**Sample JSON — `goes-beyond` (our side covers, their side does not):**

```json
{
  "summary": "OpRes PD requires appointing a single accountable officer for operational resilience; RMiT PD contains no equivalent single-officer requirement.",
  "source_clauses": [
    {
      "clause_number": "Operational Resilience 6.3",
      "text": "The board shall appoint a single senior officer who is accountable for the institution's operational resilience arrangements."
    }
  ],
  "target_clauses": [],
  "scope_note": null,
  "supported": true,
  "label": "goes-beyond",
  "sentiment": null
}
```

### Migration Notes

The retired trace at `data/artifacts/connection-trace-opres-v1-2025-draft__open-finance-v1-2025-ed.json` was generated with the old prompt; its twelve supported linkages use narrative language ("adopts", "adapts", "deviates", "silent on", "extends", etc.) rather than explicit labels. The `scripts/backfill_taxonomy.py` script re-labels the trace in place by matching summary wording against the mapping table below. No LLM is invoked — the mapping is deterministic string inference over the existing summaries.

| Old wording in summary                                           | New `label`      | Sentiment applied |
| ---------------------------------------------------------------- | ---------------- | ----------------- |
| "adopts", "duplicates", "duplication", "same as", "mirrors"      | `aligns-with`    | `None`            |
| "adapts", "tightens", "stricter", "narrower"                     | `differs-on`     | `tighten`         |
| "loosens", "wider", "broader permission"                         | `differs-on`     | `loosen`          |
| "scoping", "carves out", "orthogonal divergence"                 | `differs-on`     | `neutral`         |
| "deviates", "conflicts", "incompatible", "cannot both be met"    | `conflicts-with` | `None`            |
| "silent on", "does not address", "our side does not cover"       | `silent-on`      | `None`            |
| "extends", "goes beyond", "our side covers, their side does not" | `goes-beyond`    | `None`            |

Ambiguous summaries (no keyword match) are written back with `label: null` and flagged in a `_backfill_review.md` sidecar file for manual review. The script must not fabricate a label when the source wording does not support one.

## Architecture Notes

- **New dependencies:** none.
- **Existing dependencies:** unchanged. The finder/critic Azure AI Foundry seam, the clause index, and the citation validator all keep their current interfaces. The only signature growth is inside the `Connection` / `UnsupportedConnection` TypedDicts and the JSON schema the two prompts describe.
- **Dependencies & integration:** every downstream screen in the epic (workstream graph edge detail, review linkages, task pairwise comparison, drafting workspace) depends on the widened schema. Shipping this story first means downstream stories consume the new fields directly rather than being written against the old vocabulary and reworked.

## Exemplar Files

- `engine/connections.py` — the file to modify. Primary edit sites:
  - Lines 43-88: `Connection` and `UnsupportedConnection` TypedDict definitions and the `FinderFn` / `CriticFn` shape.
  - Lines 293-331: `FINDER_SYSTEM_PROMPT` and `CRITIC_SYSTEM_PROMPT`.
  - Lines 353-379 (`_parse_candidate_list`): candidate-shape validation.
  - Lines 177-237 (`_validate_candidates`): propagate `label` and `sentiment` into the built records.
  - Lines 260-290 (`_write_trace`): record the new fields on each validation entry.
- `engine/tests/test_connections.py` — the pattern for stubbed `finder_fn` / `critic_fn` unit tests, verbatim-anchor fixtures, and tmp-dir trace assertions. Extend with the new tests listed under Test Scenarios below.

## Implementation Plan

### Sub-tasks

**Task 1: Bump `requires-python` to `>=3.12`.** — _small_ (<10 LOC)

- Files: `pyproject.toml`.
- INDEPENDENT.
- Notes: enables `Literal[...]` and `Optional[Literal[...]]` at module import time without a `from __future__ import annotations` dance.

**Task 2: Widen `Connection` and `UnsupportedConnection` TypedDicts.** — _small_ (<50 LOC)

- Files: `engine/connections.py` (lines 43-88 region).
- INDEPENDENT.
- Notes: add `label` (required on `Connection`, optional on `UnsupportedConnection`) and `sentiment` (optional, must be `None` unless `label == "differs-on"`). Import `Literal` from `typing`. Leave `_MESSAGE_NO_CLAUSE` unchanged.

**Task 3: Update finder + critic prompts and add prompt-schema unit tests.** — _medium_ (100–300 LOC)

- Files: `engine/connections.py` (lines 293-331), `engine/tests/test_connections.py`.
- SEQUENTIAL — depends on Task 2.
- Notes: rewrite both system prompts to state the five-label taxonomy, the sentiment-only-on-`differs-on` rule, and the direction convention (document A is "we/ours"). Update the documented JSON schema inside the prompt strings. Add unit tests that stub `finder_fn` / `critic_fn` returning candidates in the new shape and assert `find_connections` produces the correct `Connection` records.

**Task 4: Extend `_parse_candidate_list` and `_validate_candidates` to enforce label + sentiment schema.** — _medium_ (100–300 LOC)

- Files: `engine/connections.py` (lines 177-237 and 353-379).
- SEQUENTIAL — depends on Task 2 and Task 3.
- Notes: raise `LLMResponseError` when `label` is missing, when `label` is outside the five-value set, when `sentiment` appears on a non-`differs-on` candidate, or when `sentiment` is outside the three-value set. Propagate the parsed `label` and `sentiment` into every built `Connection` and `UnsupportedConnection`. Do NOT touch the clause-resolution logic — that remains the verbatim-citation guardrail.

**Task 5: Extend `_write_trace` to include labels and sentiments in the validation record.** — _small_ (<50 LOC)

- Files: `engine/connections.py` (lines 260-290).
- SEQUENTIAL — depends on Task 4.
- Notes: each entry in the `validation` list gains `label` and `sentiment` fields alongside the existing `summary`, `cited_clauses`, and `supported`. Trace file remains one JSON object per pair.

**Task 6: One-off backfill script for the retired trace.** — _small_ (<100 LOC)

- Files: `scripts/backfill_taxonomy.py`, `data/artifacts/connection-trace-opres-v1-2025-draft__open-finance-v1-2025-ed.json`.
- INDEPENDENT once Task 5 is done (only depends on the widened schema being defined).
- Notes: read the retired trace, apply the deterministic mapping table from Migration Notes to each of the twelve supported findings' summary strings, write back to the same path. No LLM calls. Ambiguous entries get `label: null` and are listed in a `_backfill_review.md` sidecar file for manual review.

### Negative Constraints

- Do NOT touch `_validate_candidates`'s clause-resolution logic (the `clause_index.get(number) is not None` loop and its downstream branches). That is the verbatim-citation guardrail and belongs to the engine's foundational story.
- Do NOT touch `_cite`. Verbatim clause text still comes from `ClauseIndex` only; the model never contributes clause text.
- Do NOT re-run the finder or critic LLM against the retired trace. The backfill script is a deterministic string mapping. Any candidate the mapping cannot resolve unambiguously must land in the `_backfill_review.md` sidecar, not in a synthesised label.
- Do NOT introduce a semantic "label" attribute on graph edges. This story labels findings only. Graph edges retain their four structural types (`supersedes`, `references`, `contributes-to`, `parallel-to`) — those live in the workstream-graph story, not here.
- Do NOT change the network seam (`FinderFn` / `CriticFn`) or the `find_connections` public signature. Tests must continue to pass their stubs through unchanged.

## Test Scenarios

Implementation-level unit tests to add in `engine/tests/test_connections.py`. These are separate from the Gherkin Key Scenarios above, which describe business behaviour.

**Test: `test_widened_connection_typeddict`**

- Setup: import `Connection` and `UnsupportedConnection` from `engine.connections`.
- Action: construct a `Connection` literal with `label="aligns-with"` and `sentiment=None`, and construct another with `label="differs-on"` and `sentiment="tighten"`.
- Expected: both construct successfully; `typing.get_type_hints` reports `label` and `sentiment` with the expected `Literal` types.

**Test: `test_parse_rejects_missing_label`**

- Setup: raw JSON string `'[{"summary": "x", "source_clauses": ["RMiT 17.1"], "target_clauses": ["Outsourcing 12.1"]}]'` — a candidate with no `label` field.
- Action: call `_parse_candidate_list` on the raw string.
- Expected: raises `LLMResponseError` with a message that names the missing `label` field. No candidate is returned.

**Test: `test_parse_rejects_sentiment_on_nondiffers`**

- Setup: raw JSON with a candidate carrying `label="aligns-with"` and `sentiment="tighten"`.
- Action: call `_parse_candidate_list` on the raw string.
- Expected: raises `LLMResponseError` with a message that names the invalid sentiment-on-non-`differs-on` combination.

**Test: `test_parse_accepts_sentiment_on_differs`**

- Setup: raw JSON with a candidate carrying `label="differs-on"` and `sentiment="tighten"`.
- Action: call `_parse_candidate_list` on the raw string.
- Expected: returns one candidate dict with both fields preserved intact. No exception raised.

**Test: `test_direction_flip_swaps_silent_and_goesbeyond`**

- Setup: two hand-built documents (doc A with a governance officer clause, doc B without) plus a `ClauseIndex` covering both. Stub `finder_fn` to emit a candidate labelled `goes-beyond` when called as `(A, B)` and `silent-on` when called as `(B, A)` — mimicking a correctly-oriented model.
- Action: call `find_connections("A", "B", ...)` then `find_connections("B", "A", ...)` with the same stubs.
- Expected: the first run's supported finding is labelled `goes-beyond`; the second run's supported finding is labelled `silent-on`. Cited clauses are unchanged.

**Test: `test_retired_trace_backfill`**

- Setup: copy `data/artifacts/connection-trace-opres-v1-2025-draft__open-finance-v1-2025-ed.json` to a tmp path.
- Action: invoke `scripts/backfill_taxonomy.py` against the tmp copy.
- Expected: the rewritten trace contains all twelve original supported linkages, each with a `label` drawn from the five-value set (or `null` in the sidecar-review case), zero fabricated citations, and zero originally-supported linkages dropped. Every `sentiment` field is `None` unless the corresponding `label` is `differs-on`.

## Acceptance Criteria

- [ ] `Connection` and `UnsupportedConnection` TypedDicts carry `label` and `sentiment` fields with the correct `Literal` types.
- [ ] `FINDER_SYSTEM_PROMPT` and `CRITIC_SYSTEM_PROMPT` describe the five-label taxonomy, the sentiment-only-on-`differs-on` rule, and the fixed direction convention.
- [ ] `_parse_candidate_list` raises `LLMResponseError` on missing labels, labels outside the five-value set, sentiments on labels other than `differs-on`, and sentiments outside the three-value set.
- [ ] `_validate_candidates` propagates `label` and `sentiment` into every built `Connection` and `UnsupportedConnection` without touching clause-resolution logic.
- [ ] `_write_trace` records `label` and `sentiment` on every entry in the `validation` list.
- [ ] `scripts/backfill_taxonomy.py` rewrites the retired trace in place, preserving all twelve supported linkages under the new taxonomy with zero fabricated content.
- [ ] All existing tests in `engine/tests/test_connections.py` still pass.
- [ ] All new unit tests listed under Test Scenarios pass.
- [ ] No `mypy` regressions beyond the accepted third-party stub baseline.

## Verification

Backend-only story — no browser or UI testing.

### Backend Tests

Run:

```
pytest engine/tests/test_connections.py -v
```

- Existing tests (`test_finder_critic_two_agent_loop`, `test_critic_output_unresolved_clause_flagged`) must continue to pass — they exercise the finder/critic seam and the verbatim-citation guardrail, both of which are unchanged in behaviour.
- New tests: `test_widened_connection_typeddict`, `test_parse_rejects_missing_label`, `test_parse_rejects_sentiment_on_nondiffers`, `test_parse_accepts_sentiment_on_differs`, `test_direction_flip_swaps_silent_and_goesbeyond`, `test_retired_trace_backfill`.

### Manual Verification

- [ ] Run `scripts/backfill_taxonomy.py` once against the retired trace; confirm the resulting file contains twelve supported linkages, every one carrying a `label` (or landing in the sidecar review file with rationale), and no invented clause text.
- [ ] Inspect the rewritten trace by eye against the mapping table to catch any keyword-match false positives before the demo relies on it.

## Open Questions

All open questions listed in the business sections above are either resolved or deferred as non-blocking. No new technical open questions arise from this section.
