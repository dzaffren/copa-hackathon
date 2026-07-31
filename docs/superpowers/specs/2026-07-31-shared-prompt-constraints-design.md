# Shared Prompt Constraints — Governing Thought, MECE, Action Titles

**Date:** 31 Jul 2026
**Status:** built, verified against a live A/B run
**Supersedes nothing.** Extends
[`docs/specs/plain-language-finding-explanations/spec.md`](../../specs/plain-language-finding-explanations/spec.md),
whose word caps and code-layer enforcement stay exactly as they are.

Findings and Copilot replies are still hard to read on the first pass. The
previous round made the _language_ plain; this round makes the _structure_
plain. Four writing constraints borrowed from consulting practice — lead with
the answer, don't overlap or omit, make headings carry the insight, cut
everything that carries neither — are stated once and shared by every prompt
that explains something to the drafter.

> **Two corrections from the live A/B run, recorded because both changed the
> design.** First, the first build leaked `Document A` / `Document B` into 10 of
> 15 drafter-visible `scope_note`s; that needed a fifth constant and two new
> guards, described under "The internal-label regression" below. Second,
> **shorter is not a goal** — the drafter's constraint is comprehensibility, and
> a longer summary that names what each side actually does beats a shorter vague
> one. The 20/30-word caps stay as an anti-rambling backstop, not a target.

## The problem this solves

The prior fix capped `summary` at 20 words and `scope_note` at 30, and told the
Copilot to write plain English. That worked on vocabulary and sentence length.
It did not fix three remaining failures:

- **Buried answers.** A Copilot reply builds toward its conclusion instead of
  opening with it, so the drafter reads three paragraphs to find out whether the
  clause needs changing.
- **Topic headings.** Headings name a subject ("Exit planning", "Cost analysis")
  rather than the finding, so scanning the reply tells the drafter nothing.
- **Overlapping findings.** Nothing in the finder prompts says two findings in a
  batch must not describe the same underlying relationship, or that a genuine
  one must not be skipped.

## What changes

### A new module: `engine/prompt_style.py`

Five string constants. Two are shared by both prompt surfaces, three are
surface-specific:

| Constant                                                                     | Used by      |
| ---------------------------------------------------------------------------- | ------------ |
| `GOVERNING_THOUGHT_RULE` — lead with the single claim being made             | both         |
| `HOUSE_CONSTRAINTS` — MECE, tone, no fluff, no em dashes                     | both         |
| `ACTION_TITLES_RULE` — a heading states the insight, not the topic           | Copilot only |
| `EVIDENCE_DISCIPLINE_RULE` — the summary must be provable from cited clauses | finders only |
| `NO_INTERNAL_LABELS_RULE` — never name a side by letter                      | finders only |

One source of truth is the point. Three prompts previously banned em dashes in
three slightly different sentences; that drift is the thing being fixed, and
`test_the_em_dash_ban_is_stated_exactly_once` now holds the line. The module
holds text only — no functions, no imports from elsewhere in `engine/`, so
nothing can create a cycle, asserted by
`test_prompt_style_holds_no_engine_imports`.

### `engine/copilot.py` — the chat prompt

`_system_prompt`'s `WRITING STYLE:` block is replaced by the two shared
constants. The plain-language sentence and the em-dash ban already in that block
are absorbed into `HOUSE_CONSTRAINTS` rather than repeated. On this surface the
constraints read as:

- **Governing thought** — the first sentence of a substantive reply _is_ the
  answer. No warm-up, no restating the question, no "let me look at that".
- **MECE** — grouped bullets and sections must not overlap, and must not omit a
  branch the drafter needs.
- **Action titles** — a Markdown heading states the insight, not the topic:
  "Outsourcing 12.1 requires a tested exit plan; the draft does not", never
  "Exit planning".
- **No fluff** — every sentence carries a claim or the evidence for one.

Proposed clause text the Copilot drafts for the document keeps its formal policy
register; the constraints govern the _explanation to the drafter_, which is the
part that was unreadable. That distinction already exists in the current prompt
and is preserved verbatim.

### `engine/arm_g.py` — the two finder prompts

`SAME_TOPIC_FINDER_SYSTEM_PROMPT` and `COVERAGE_FINDER_SYSTEM_PROMPT` emit JSON,
not prose, so the constraints land on field content rather than on layout:

- **Governing thought** — the `summary` _is_ the governing thought: the single
  claim the finding makes. This sharpens the existing "do not merely restate the
  label" rule into a positive instruction rather than a prohibition.
- **MECE (new)** — within one batch, do not emit two findings describing the same
  underlying relationship between the same clauses, and do not skip a genuine
  one. Nothing in either prompt says this today, and the risk is structural
  rather than hypothetical: `BATCH-UNION MEMBERSHIP` explicitly permits relating
  any A-side anchor to any B-side anchor, so two overlapping findings for one
  relationship is the natural failure mode.
- **Evidence discipline (new)** — the `summary` must be provable from the cited
  clauses alone. If the claim needs a fact that is not in `source_clauses` or
  `target_clauses`, either cite the clause that carries it or weaken the claim.
  This is the template's "evidence required to prove or disprove the hypothesis"
  step, adapted: the finding already carries its evidence in the clause arrays,
  so the useful part is the constraint that summary and evidence must match.
- **No internal labels (new, added after the A/B run)** — never write
  `Document A`, `Document B`, `A-side`, or `B-side` in `summary` or `scope_note`.
  See the next section for why this exists.
- Tone and no-fluff replace the existing near-duplicate phrasing sentences.
- Action titles do not apply: there is no heading in a finding object. The
  underlying idea — state the insight, not the topic — is already carried by the
  governing-thought rule on `summary`.

Rejected for this surface, with reasons, so the next reader does not re-litigate
them:

- **SCQ as a section structure** — there are no fields for Situation or Question,
  and a 20-word summary cannot carry three sections.
- **"Complication" as a selection lens** — an `aligns-with` finding has no
  complication by construction, so requiring one would quietly bias the finder
  against one of the five taxonomy labels.
- **Issue tree** — findings are a flat list keyed by clause pair, not a hierarchy.
- **Porter's Five Forces, 3Cs, 4Ps, profitability tree** — business-strategy
  frameworks with nothing to say about comparing two regulatory clauses.
- **"Group findings into 3 distinct pillars"** — grouping is the frontend's job,
  and exactly three is arbitrary.
- **Roadmap, next steps, risks and mitigation** — a finding states what two
  documents say; the drafter decides what to do about it. Prescribing action
  inverts the review-and-accept model.

### The internal-label regression, and the guards it added

The first build of this change shipped without `NO_INTERNAL_LABELS_RULE`, and a
live A/B run caught the result: **10 of 15 drafter-visible `scope_note`s said
"Document B does not address…"**, against 0 before the change.

The cause is proximity. Both finder prompts must carry
`DIRECTION CONVENTION (fixed): document A is 'we/ours'; document B is
'they/theirs'` — the side-guard that keeps `source_clauses` A-side and
`target_clauses` B-side depends on it. Adding `EVIDENCE_DISCIPLINE_RULE` and
`GOVERNING_THOUGHT_RULE` next to that line, both of which talk about "the cited
clauses", pulled the letter vocabulary out of the mechanics and into the prose.
The old prompts happened to avoid this by never inviting the model to reason
aloud about sides.

This matters more than it looks. Aisyah has no way to know which document is B;
"Document B is silent on governance" is strictly less useful than "the BIS paper
is silent on governance", and it looks like a leaked internal detail in a demo.

Two guards, because a prompt-level assertion alone would not have caught it:

- `test_prompt_style.py::test_finder_prompts_forbid_naming_the_sides_by_letter` —
  asserts the rule is present in both finder prompts, and that the direction
  convention it coexists with is still there.
- `test_demo_finding_phrasing.py::test_neither_field_names_a_side_by_letter` —
  the output-side half: no committed finding may name a side by letter. This is
  the one that would have caught the original leak, and it lives beside the
  existing em-dash and word-cap assertions rather than in a new module.

After the fix, the same A/B input produced 0 of 15 leaks.

### What deliberately does not change

- **The word caps and `enforce_phrasing` are untouched, but they are a backstop,
  not a target.** `SUMMARY_MAX_WORDS = 20` and `SCOPE_NOTE_MAX_WORDS = 30` stop
  the model rambling; they are not an instruction to compress. The bar the
  drafter actually cares about is comprehensibility, and a 21-word summary that
  names what each side does beats an 18-word one that gestures. `over_cap_kept`
  remains the honest signal that a human may want to reword, not a failure.
- **MECE gets no code-layer guard.** A mechanical dedupe on
  `(label, source_clauses, target_clauses)` was considered and rejected for this
  change: it widens the diff past prompts, and an exact-tuple match would catch
  only the least interesting duplicates. If overlapping findings survive in
  practice, that guard is the follow-up.
- **The SCQ scaffold, issue tree, evidence-type step, and roadmap are out of
  scope.** The complaint was that answers were hard to understand. A five-section
  consulting deck per reply adds structure the drafter has to navigate before
  reaching the point, which is the opposite of the goal. Only the constraints and
  the governing thought are adopted.
- **`engine/connections.py` is not touched.** Its `FINDER_SYSTEM_PROMPT` and
  `CRITIC_SYSTEM_PROMPT` are retained solely as a rollback seam (CLAUDE.md), so
  changing them would mean maintaining a path nothing calls.
- **No committed findings are regenerated.** The demo runs build-and-persist off
  findings committed with each workstream. Rewording those is a separate,
  model-calling exercise; this change affects what the next analysis produces.

## Verification

**Tests: 958 passed, 1 skipped** via `.venv/bin/python -m pytest engine/tests`,
from an 814-pass baseline. (The forge `stop-verify` hook reports `LINT FAIL: No
module named ruff` throughout; that is the documented false-fail in
`docs/learnings/blocker-forge-verify-hook-false-fail-pyenv-ruff.md`.)

`engine/tests/test_prompt_style.py` is new, in the house style of
`test_connections.py:836` — parametrized over the three live prompts
(`SAME_TOPIC_FINDER_SYSTEM_PROMPT`, `COVERAGE_FINDER_SYSTEM_PROMPT`, and
`copilot._system_prompt`'s output). Beyond the shared-constraints assertion it
locks down four things worth naming: the em-dash ban appears exactly once per
prompt, the finders keep their word caps, `ACTION_TITLES_RULE` is Copilot-only,
and the citation rules survive sharing prompt space with the style block.

The existing suite stayed green as predicted: `test_arm_g.py:376` asserts prompt
identity by reference (`system == arm_g.COVERAGE_FINDER_SYSTEM_PROMPT`), not by
content, so rewriting the text does not break it.

**Live A/B run, 31 Jul 2026.** Identical 8 anchor pairs
(`ed-open-finance-2025` × `bis-papers-168` in `open-finance-pd-2026`), same
models, same code; the old prompt strings were monkeypatched in from a detached
worktree at `HEAD` so the prompt was the only variable.

| Metric                         | OLD  | NEW (first build) | NEW (after fix) |
| ------------------------------ | ---- | ----------------- | --------------- |
| Internal-label leaks           | 0    | **10/15**         | **0/15**        |
| Summaries over the 20-word cap | 4/16 | 6/15              | 0/15            |
| Same-topic findings            | 5    | 5                 | 4               |
| Coverage findings              | 11   | 10                | 15              |

Prompt size is the standing cost: `SAME_TOPIC` grew ~671 → ~1014 tokens,
`COVERAGE` ~732 → ~1070, Copilot ~774 → ~1014, paid on every call.

**Do not read the finding counts as a result.** Coverage output varies run to run
on identical input: four calls of the same prompt returned 0, 14, 11, and 15
findings. Only the leak count (consistent across runs) and the word counts are
reliable signals here; any future claim about finding volume needs several runs
averaged, not one.

**Still unverified: the Copilot surface.** Every measurement above is from the
finder prompts. No live Copilot turn was run, so whether `ACTION_TITLES_RULE` and
the governing-thought rule improve a chat reply is asserted by construction only.
Given that the finder surface leaked internal vocabulary on its first build, the
Copilot prompt deserves the same empirical check before the demo.

## Risks

- **Prompt bloat — measured, not mitigated.** The design intended to "keep the
  shared text short"; it did not. Every prompt grew 31–51% (~671 → ~1014 tokens
  for `SAME_TOPIC`, ~732 → ~1070 for `COVERAGE`, ~774 → ~1014 for Copilot), paid
  on every call. The constraints do sit after, never interleaved with, the
  grounding and citation rules, and `test_the_citation_rules_survive_the_style_block`
  asserts those rules are still present. If token cost becomes a problem,
  `HOUSE_CONSTRAINTS` is the block to trim first.
- **Sharper claims invite overclaiming.** `GOVERNING_THOUGHT_RULE` and
  `ACTION_TITLES_RULE` both ask for a stronger statement than the model would
  otherwise make, which risks a claim the clauses do not support.
  `EVIDENCE_DISCIPLINE_RULE` exists to counterweight this on the finder surface;
  on the Copilot surface the backstop is the unchanged verbatim citation rule and
  `_validate_reply`'s deterministic citation filter.
- **Proximity effects are the failure mode to watch.** The internal-label leak was
  not a wrong rule, it was a right rule placed next to `DIRECTION CONVENTION`,
  which pulled that section's vocabulary into the output. Adding anything to these
  prompts warrants a live A/B and a look at the rendered text, not just a green
  suite.
