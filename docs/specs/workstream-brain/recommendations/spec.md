# Recommendations

**Ticket:** None — this repo has no issue tracker (see `CLAUDE.md`)

## Summary

Aisyah has spent an afternoon accepting linkages: this clause differs from HKMA's, that one goes beyond BIS, this third is silent where RMiT is not. She now holds thirty accepted findings and no answer to the only question that matters — **so what should the policy document actually say?** This epic turns her accepted findings into written recommendations: each one naming what to do, why, and which clause it rests on. She bookmarks the ones worth taking forward, comments on the ones that miss, and finds her selection beside the draft when she writes.

Two things make it more than a generator. Recommendations are formulated on **dimensions Aisyah chooses herself** — the policy requirements she records on the working draft — so the tool does not invent its own categories. And the rules the engine follows become **guardrails** she can read and edit, behind a protection badge on the card that generates from them, so its judgement is accountable to her rather than fixed.

Alongside it, the drafting workspace's Reviewed tab becomes a **Playbook**: one free-text section per Copilot stage, where Aisyah records the questions she wants brainstormed, the structure a draft should follow, how she writes, and who signs off. Two configuration surfaces, each sitting next to the thing it configures.

## Background & Context

**Current state:**

- Aisyah opens a working draft's task screen and sees three things: a **Source card** repeating the document's name, owner, reviewers and status (all but one line of which the page header already shows), a Neighbour nodes card, and the Pairwise findings box.
- In the Pairwise findings box she works through every AI-found linkage in the draft's neighbourhood — on the 2026 Open Finance policy document, 130 of them — accepting the ones she agrees with and dismissing the rest.
- Her accepted findings then appear in one place: a **Reviewed** tab beside the draft, as a read-only reference list.
- Every finding is a comparison between two clauses. None of them is a recommendation. Nothing in the tool says what to _do_.
- Each document carries a Regulatory profile including a **Policy requirement** field, which the tool already tells her "become the dimensions the Recommendations feature is formulated on" — a promise the tool does not yet keep.

**Problem:**

- **The tool stops one step short of useful.** Aisyah finishes triage holding a pile of accepted comparisons and still has to synthesise them into policy positions by hand, which is the actual work. The tool has done the reading and left her the thinking.
- **Thirty findings do not fit in a head.** A finding says "our clause 8.4 is silent where HKMA's 4.2 is not". Ten such findings across consent, liability and API security are a theme; the tool shows them as a flat list and never draws the theme.
- **What was learned once is learned again.** When Aisyah judges a recommendation wrong — because HKMA's "TSP" is not our "TPSP", or because PayNet already owns the implementation timetable — that knowledge lands nowhere. The next batch makes the same mistake.
- **The tool's judgement is not accountable.** It will decline to recommend some things and insist on others for reasons Aisyah cannot read, question, or change.
- **A card earns its space or loses it.** The Source card duplicates the page header and shows nothing Aisyah acts on, while occupying the most valuable column on the task screen. The Reviewed tab duplicates the task screen beside the editor.

**Evidence this is the right problem.** A real BNM policy officer was given nine AI-generated recommendations against the Open Finance Exposure Draft and scored each 1–5 for usefulness, with written comments. Seven scored 3 or above; the reasons the others fell short are specific, repeatable, and are what shapes this epic's guardrails. That review is reproduced in full in **Appendix A**.

## Goals

- Turn Aisyah's **accepted findings** into written recommendations — what to do, why, and on which clause — without her leaving the task screen.
- Formulate them on the **policy requirements she records herself**, so the tool reasons on her dimensions rather than its own.
- Show her which accepted findings **no recommendation drew on**, so a coverage gap is visible rather than silent.
- Let her **bookmark** the ones worth taking forward, and keep them safe when she regenerates.
- Let her **comment** on one that misses and **rewrite** that card alone, without discarding a set she is otherwise happy with.
- Give the engine's rules a **visible, editable home** she alone authors, pre-populated so it is useful from the first day.
- Let her **configure each Copilot stage** in her own words, so house conventions are stated once rather than every session.
- Give the tool's rules a **visible, editable home** that conditions both the recommendations and the Copilot.
- Reclaim the task screen's left column and the drafting workspace's first tab.

## Non-Goals

- **Scoring recommendations for usefulness.** The tool writes recommendations; Aisyah judges them. A confidence score presented next to model output invites the drafter to trust the number instead of reading the evidence, and the 1–5 scores in Appendix A were produced by a human reviewer, not a machine.
- **Writing policy text anywhere but the Copilot.** A recommendation says what should change and why. Turning that into clause language happens in the Copilot conversation, where every word is reviewed before it lands. Nothing else may write to the draft — no insert button, no hand-off action.
- **Recommending from findings Aisyah has not accepted.** Dismissed and untriaged findings are not evidence.
- **Cross-workstream recommendations.** Scope is one working draft and its neighbourhood, matching the Pairwise findings box exactly.
- **Reworking the Regulatory profile form.** The Policy requirement field already exists, is already a comma-separated list, and already carries the note explaining what it feeds. This epic consumes it.
- **Recommendations on published documents.** Only a working draft has something to change.

## Story Index

| Ticket | Story                                               | Spec                                                                                             | Type        | Status      | Dependencies                              |
| ------ | --------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ----------- | ----------- | ----------------------------------------- |
| None   | Recommendations from my accepted findings           | [spec-recommendations-from-accepted-findings.md](spec-recommendations-from-accepted-findings.md) | User-facing | Not Started | —                                         |
| None   | Bookmark recommendations and carry them to my draft | [spec-bookmark-and-carry-forward.md](spec-bookmark-and-carry-forward.md)                         | User-facing | Not Started | Recommendations from my accepted findings |
| None   | Comment on a recommendation and have it rewritten   | [spec-comment-and-rewrite.md](spec-comment-and-rewrite.md)                                       | User-facing | Not Started | Recommendations from my accepted findings |
| None   | A Playbook that configures the Copilot              | [spec-playbook.md](spec-playbook.md)                                                             | User-facing | Not Started | —                                         |
| None   | One name for the regulatory profile store           | [spec-metadata-store-rename.md](spec-metadata-store-rename.md)                                   | Technical   | Not Started | —                                         |

Story 1 is the vertical slice that makes the feature real: Aisyah generates recommendations, reads them, and edits the guardrails they follow. Stories 2 and 3 each add one capability on top and are independent of each other. Story 4 is genuinely independent — the Playbook configures the Copilot and touches no part of the recommendations flow. Story 5 is a behaviour-preserving rename touching the store Story 1 reads from; it carries no user-visible change and ships in the same change set as Story 1 so the new code is written against the corrected name once.

The two configuration surfaces are deliberately separate and must not be confused: **guardrails** (Story 1, on the Recommendations card) steer the recommendations engine; the **Playbook** (Story 4, in the drafting workspace) configures the Copilot's five stages. Neither reads the other.

## Shared Business Rules

- **Policy requirements are the dimensions, and they are required.** The working draft's own Policy requirement field supplies them, split on commas. It is not read from neighbouring documents. With none recorded, the tool will not generate — it says so and offers the way to set them. This is checked when Aisyah generates, not when she saves a profile: a half-filled profile must still be saveable.
- **Only accepted findings are evidence.** Scope is the working draft's whole neighbourhood — the same set the Pairwise findings box already uses, so the surfaces can never disagree about what is in scope.
- **Every recommendation quotes its evidence word-for-word.** Each names the accepted findings it rests on and reproduces their clause numbers and clause text exactly. A recommendation with no supporting accepted finding is not written at all. This is the repo's standing citation rule; it is a property of how citations are produced, not a preference, and nothing in this epic — including the Playbook — can switch it off.
- **An accepted finding no recommendation drew on is shown, not hidden.** Coverage is reported against **every generated recommendation**, consistently on both surfaces, so the number means the same thing wherever Aisyah reads it.
- **A recommendation carries a note about what it could not verify.** Some of what makes a recommendation right or wrong exists only in people's heads — that a platform operator already owns an implementation plan, that two policy documents sit with different departments. The tool states its unverified assumptions rather than writing confidently past them.
- **Bookmarks survive regeneration; nothing else does.** Regenerating keeps every bookmarked recommendation exactly as it was and replaces all the rest. Bookmarked ones are also shown to the tool as already taken forward, so the new batch does not restate them in different words.
- **A comment stays on its card; a standing rule is Aisyah's deliberate act.** A comment informs its own recommendation's rewrite and is available to the Copilot, and goes with the card when a regeneration replaces it. Making a correction permanent means recording it in the guardrails herself. Nothing is promoted, re-worded, or copied there on her behalf — a tool that re-interpreted her comments into rules would be authoring what it then follows, and an over-broad rule would suppress good recommendations invisibly.
- **Guardrails steer the recommendations engine; the Playbook configures the Copilot.** Each belongs to the workstream, each is free text, each ships ready to use, and neither reads the other. Pairwise analysis reads neither.
- **Only the Copilot writes to the draft.** Everything that lands on the page arrives through the Copilot conversation and is reviewed there. No surface in this epic inserts text or hands work to the Copilot on Aisyah's behalf.

### The five default guardrails

Derived directly from the reviewer's comments in Appendix A. They are the starting content of every workstream's **guardrails** — visible from the first day behind the Recommendations card's protection badge, and fully editable. Nothing here is protected: a rule the drafter cannot change is not accountable to her.

| #   | Guardrail                    | Drawn from               | The rule                                                                                                                                                                                                                                                                                    |
| --- | ---------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **House convention**         | Row 4, scored **1/5**    | Never recommend that a policy document cite another policy document by specific provision number. BNM policy documents cross-reference each other in general terms deliberately, because provision numbering shifts when a document is reissued and a pinned reference silently goes stale. |
| 2   | **Scope boundary**           | Row 2, scored 3/5        | Recommend only within the applicability the draft itself states. Do not propose obligations on classes of entity the instrument does not cover.                                                                                                                                             |
| 3   | **Terminology false-friend** | Row 1, scored 3/5        | Before asserting a difference against a peer regulator, establish that a shared term means the same thing on both sides. Where it cannot be established from the documents, say so instead of asserting the difference.                                                                     |
| 4   | **Alignment from silence**   | Row 9, scored 4/5        | Where two documents are both silent or both high-level on a point, report that neither elaborates. Mutual vagueness is not agreement, and describing it as agreement overstates how closely the draft tracks an international standard.                                                     |
| 5   | **Evidence floor**           | The repo's citation rule | Every recommendation rests on at least one accepted finding, named, with its clause number and clause text reproduced word-for-word. Nothing is written that the accepted evidence does not support.                                                                                        |

Guardrails 1–4 are the four distinct ways the sample recommendations failed. Rows 5 and 6 failed a fifth way that no guardrail can fix — the reviewer knew things no document contains — which is why every recommendation carries its unverified assumptions instead.

## User Journey Map

1. **She records what the document is about.** Opening the 2026 Open Finance policy document's profile, Aisyah types into Policy requirement: `consent management, third party oversight, liability allocation, API security, phased implementation`. The form already tells her these become the dimensions recommendations are formulated on. _(Prerequisite — the field exists today)_
2. **She triages linkages.** In the Pairwise findings box she works through the neighbourhood's findings, accepting 30 and dismissing the rest. _(Existing behaviour)_
3. **She generates.** Where the Source card used to sit there is now a Recommendations card. She presses Generate. It reports what it is working from — 30 accepted findings across 5 dimensions — and returns seven recommendations. _(Story: Recommendations from my accepted findings)_
4. **She reads one.** The first says to publish and maintain a list of authorised data consumers. It gives its reasoning, states the action for BNM, and lists the three accepted findings behind it — expandable to the clauses themselves, quoted in full with their numbers. An information marker beside the title reveals what the tool could not verify. _(Story: Recommendations from my accepted findings)_
5. **She checks what was left out.** Below the recommendations, a collapsed section reports that 7 of her 30 accepted findings were not drawn on by anything. She expands it, reads two, and agrees neither warrants a policy change. _(Story: Recommendations from my accepted findings)_
6. **She finds one that misses.** A recommendation claims a gap on third party service providers. Aisyah knows the peer regulator's term means something different from ours. She comments: _"HKMA's TSP is closer to our data consumer — our TPSP is an operational vendor. Different concepts."_ She presses Rewrite; the card is rewritten from her correction and keeps its place. _(Story: Comment on a recommendation and have it rewritten)_
7. **She makes that correction permanent.** The terminology point will keep recurring, so she opens the guardrails behind the card's protection badge. They already hold the five defaults in plain language; she adds her own rule beneath them and saves. Nothing put it there for her. _(Story: Recommendations from my accepted findings)_
8. **She bookmarks four.** Four are worth taking forward. She bookmarks them; they move to the top of the card. _(Story: Bookmark recommendations and carry them to my draft)_
9. **She accepts more findings and regenerates.** Later she accepts twelve more findings and generates again. Her four bookmarks are untouched. The new batch does not restate them, and none of them repeats the terminology mistake — because she recorded it as a guardrail. _(Stories: Bookmark…; Recommendations…)_
10. **She opens the draft.** The tabs read **Recommendations**, **Playbook**, **Copilot**. The first holds her four bookmarks, with the not-yet-reflected count beneath them. _(Story: Bookmark recommendations and carry them to my draft)_
11. **She configures the Copilot.** In the Playbook she finds a section for each of its five stages. The first, `/explore-task`, is locked — it reads the document's own recorded profile, and she is shown where that is maintained. Under `/brainstorm` she seeds the three questions she has been carrying; under `/draft`, the standard policy-document skeleton; under `/write`, that obligations read "must" and guidance "should"; under `/deliver`, that policy sign-off comes first, then legal, then the Deputy Governor's office. _(Story: A Playbook that configures the Copilot)_
12. **She drafts.** In the Copilot she asks for clause language for her first bookmarked recommendation. It follows her Playbook without her restating any of it, and she reviews every word before it reaches the page. _(Existing behaviour, conditioned by Story: A Playbook that configures the Copilot)_

## Success Metrics

- **Aisyah leaves the task screen with a written position, not a pile of comparisons.** Success is that the journey above completes end-to-end on the 2026 Open Finance policy document.
- **A correction can be made once.** After Aisyah records a rule in the guardrails, no later batch repeats the mistake it covers. Note the "can": the recording is her deliberate act, not something the tool infers. The epic's claim is that a lasting correction is now _possible and visible_, not that it happens automatically — see the resolved question on why nothing writes to the guardrails but her.
- **Every recommendation on screen can be traced to a quoted clause.** No recommendation appears that does not name at least one accepted finding and reproduce its clause text.
- **Nothing the tool does is unaccountable.** Every rule shaping what it writes — the engine's guardrails and the Copilot's Playbook — can be read, and changed, by the drafter.
- **A convention is stated once.** After Aisyah configures a Copilot stage, she does not restate that instruction in the conversation again.

## Dependencies

- **The demo workstream's profile is seeded — this prerequisite is met.** `data/workstreams/open-finance-pd-2026/metadata/open-finance-pd-2026-pd.json` records the working draft's profile with six policy requirements: Governance; Participation and scope of information sharing; Transition arrangements; Consent management; Customer protection; Management of technology risk. Those are the dimensions recommendations are formulated on. It was seeded into `concepts/` and moved to `metadata/` by the rename story, so the demo reads canonically rather than through the fallback. The five context documents in that workstream have no profile, which is expected — only the working draft's requirements are read.
- **A model call.** Generating and rewriting call a model, as the existing pairwise analysis already does. As with analysis, the demo runs from committed pre-generated output so no model call is needed on the day, and the test suite injects a stub so continuous integration needs no credentials.
- **No new external systems, and no new dependencies** in either the engine or the frontend.

## Rollout Strategy

Everything is behind the drafter's own action — nothing generates on load — so there is no phased release and no communication plan. This is a prototype with one drafter persona and no external users.

Suggested build order:

1. **One name for the regulatory profile store** first and quickly, so the new code is written against the corrected name once rather than renamed afterwards.
2. **Recommendations from my accepted findings**, together with the demo profile and pre-generated output. At this point the feature is demonstrable.
3. **A Playbook that configures the Copilot** next, because it removes the tab the next story's tab order assumes is gone. Otherwise independent — it can be built by a second person in parallel from the start.
4. **Bookmark recommendations and carry them to my draft** and **Comment on a recommendation and have it rewritten** in parallel — they touch different parts of the card and do not depend on each other.

---

## Dependencies & Integration

- **Affected features:** the task screen (loses `SourceCard`, gains the Recommendations card and its guardrails), the drafting workspace (loses the Reviewed tab, gains Recommendations and Playbook), the Copilot (each stage gains its Playbook section as standing context), and the Regulatory profile store, which is renamed. The Pairwise findings box and the review screen are read from but not modified. The Copilot's five stages, their order and their sequential unlocking are unchanged.
- **Shared state:** a new per-task side-file `data/workstreams/{ws}/recommendations/{node_id}.json`, plus two per-workstream files — `{ws}/guardrails.json` and `{ws}/playbook.json` — all following the existing `findings/`, `linkage_review/` and `drafts/` pattern. The regulatory-profile store moves from `{ws}/concepts/` to `{ws}/metadata/`.
- **Breaking changes:** none on the API surface. The rename is internal; the node-detail response is unchanged in both shape and field names.
- **A route changes consumer, not purpose.** The reviewed-linkages projection stops backing a tab and becomes the recommendation engine's evidence input — the same accepted-findings-across-the-neighbourhood set, read server-side instead of rendered.
- **Migration path:** none required. The renamed profile store falls back to reading the old directory, and a workstream with no Playbook file reads the defaults, so the three retired workstreams stay byte-identical on disk.

## Shared Data Model

**Recommendations** (`{ws}/recommendations/{node_id}.json`) — new file, written the first time Aisyah generates:

| Field             | Type              | Description                                                                           |
| ----------------- | ----------------- | ------------------------------------------------------------------------------------- |
| `generated_at`    | timestamp \| null | When the current set was produced. `null` before the first generation.                |
| `dimensions_used` | string[]          | The policy requirements the set was formulated on, as parsed at generation time.      |
| `recommendations` | object[]          | The current set — bookmarked entries carried across regenerations, the rest replaced. |

Each recommendation mirrors the columns the reviewer in Appendix A actually worked with — **Recommendation**, **Rationale**, **Action for BNM**, **Referenced rows** — dropping _Type_ and _Relevance score_, and adding four fields this epic introduces:

| Field             | Type     | Description                                                                                                                                                                                     |
| ----------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`              | string   | Stable for the life of the recommendation. Survives a rewrite; never reused after a regeneration.                                                                                               |
| `title`           | string   | The recommendation in one line.                                                                                                                                                                 |
| `rationale`       | string   | Why, referring to what the compared documents say.                                                                                                                                              |
| `action`          | string   | What BNM should do.                                                                                                                                                                             |
| `dimensions`      | string[] | Which of the draft's policy requirements this touches. Free-form count — a recommendation may span several, and a dimension may attract several recommendations or none.                        |
| `evidence`        | object[] | The accepted findings behind it: finding identity, both endpoint documents, clause number and clause text reproduced word-for-word. Never empty.                                                |
| `confidence_note` | string   | What the tool could not verify from the documents available.                                                                                                                                    |
| `bookmarked`      | boolean  | Whether Aisyah is taking it forward.                                                                                                                                                            |
| `comments`        | object[] | Her comments on this card, each with author and timestamp. Card-scoped: they inform this card's rewrite and are available to the Copilot, and go with the card when a regeneration replaces it. |
| `revisions`       | object[] | Previous versions, appended on each rewrite, so a rewrite is auditable rather than silent.                                                                                                      |

Coverage — which accepted findings no recommendation drew on — is **derived, never stored**: the accepted set across the neighbourhood minus every finding cited by any recommendation in the file. Storing it would let it drift from the findings it describes the moment a review state changed.

**Guardrails** (`{ws}/guardrails.json`) — new file, one per workstream, written on first save:

| Field        | Type      | Description                                                                                     |
| ------------ | --------- | ----------------------------------------------------------------------------------------------- |
| `body`       | string    | The rules the recommendations engine follows, in the drafter's own words. Free text, no schema. |
| `updated_at` | timestamp | When it was last saved.                                                                         |

A workstream with no file reads the five defaults, so the guardrails are populated and useful from the first day and no workstream needs migrating. Aisyah is the only writer: no generation, comment or rewrite ever edits this file.

**Playbook** (`{ws}/playbook.json`) — new file, one per workstream, written on first save. One free-text section per Copilot stage:

| Field        | Type      | Description                                                           |
| ------------ | --------- | --------------------------------------------------------------------- |
| `brainstorm` | string    | Ideas and questions Aisyah wants to bounce off the Copilot.           |
| `draft`      | string    | The template or style guide a draft should follow.                    |
| `write`      | string    | Writing preferences and house rules.                                  |
| `deliver`    | string    | Approval and review conventions, and the approval layers to route to. |
| `updated_at` | timestamp | When it was last saved.                                               |

`/explore-task` has **no field**, deliberately: it is locked, and reads the document's own recorded regulatory profile. Storing an editable section for it would be the first step towards overriding what it reports. Every section starts **empty** — unlike the guardrails, there is no evidence base saying what a good default instruction would be, and pre-filled text a drafter did not write would be followed silently.

**Regulatory profile** (`{ws}/concepts/{node_id}.json` → `{ws}/metadata/{node_id}.json`) — location and internal function names change; **contents and API shape do not**. See Story 5.

## Shared Architecture Notes

- **`concepts` already means something else, and that is why the rename is in this epic.** The node-detail response carries _both_ a `metadata` block (the seven-field regulatory profile, read from `concepts/`) and a `concepts` block (a document's **extracted axes**, read from `axes/`). The extracted axes are the real concepts. The directory named `concepts/` is the one thing in the system that is not. Story 5 moves only the profile store; `extract-concepts`, `_node_concepts_block`, the `axes/` store and the `concepts` response block are all deliberately untouched.
- **Scope is computed by the existing neighbourhood rule, reused not reimplemented.** `workstreams.neighbourhood_edges` is what the Pairwise findings box already uses. Calling the same function is what guarantees the surfaces cannot disagree — on `open-finance-pd-2026` the working draft has exactly one edge, and that pair has no findings at all, so any narrower rule yields nothing.
- **Generation is an injected seam, as analysis already is.** A `generate_recommendations_fn` parameter on the application factory mirrors the existing `run_arm_g_fn`: defaulted to a workstream-bound adapter over the shared model client, stubbed in tests. The running service does reach a model on generate and rewrite; continuous integration never does.
- **Single pass, no critic.** Unlike the finder→critic loop in the pairwise analysis, generation is one call. The guardrails are constraints inside that call, not a second scoring stage — which is also why no relevance score reaches the interface.
- **Two configuration files, two consumers, no crossover.** The guardrails join the recommendation prompt; the Playbook's per-stage sections join the Copilot's system prompt at the matching stage. Both are prose, not schemas: nothing parses them and nothing validates them beyond a length bound. Neither reads the other, and the code paths stay separate so a change to one cannot leak into the other.
- **Reading is never an error.** Fetching recommendations before any have been generated returns an empty set with no timestamp; fetching guardrails that have never been saved returns the five defaults; fetching a Playbook that has never been saved returns empty sections. The interface's empty states are data, not error handling.
- **The locked stage is locked server-side too.** `/explore-task` has no Playbook field at all, so there is nothing to send and nothing to persist. A client that invented one would have it ignored, which is what keeps the stage's output derived from the document's recorded profile.
- **No new frontend dependency for the information bubble.** The interface library in this repo holds eight primitives and no tooltip, and the editor already hand-rolls its comment popover rather than pulling in a headless-component library. The information marker follows that existing decision, and must open on hover, on keyboard focus, and on tap.
- **Two standing repo conventions apply:** any new engine dependency must be added both to the project file and to the explicit install list in the test workflow (this epic adds none), and every write of document text passes UTF-8 explicitly — clause text carries section marks and en-dashes that the Windows platform default mangles.

## Open Questions

- [x] ~~Should recommendations carry a type such as Gap / Strength / Divergence?~~ — **Resolved: no.** The sample used four such types and the reviewer disputed one outright ("seems more like a Gap"), which is evidence the boundary is not clear even to an expert. `Gap` is also retired vocabulary in this repo. Dimensions come from Aisyah's own policy requirements instead, which she authored and therefore understands.
- [x] ~~Should the tool score each recommendation for relevance, as the reviewer did?~~ — **Resolved: no.** Generation is a single pass with no critic stage, so there is no independent judgement to report. Showing a self-assigned score would invite trust the number has not earned.
- [x] ~~Where do the dimensions come from — the draft, or its neighbours too?~~ — **Resolved: the working draft only.** Pooling neighbours' requirements would make the dimension set unpredictable and require every neighbouring document to be enriched first.
- [x] ~~Is an empty Policy requirement rejected when saving a profile, or when generating?~~ — **Resolved: when generating.** Rejecting on save would make a half-filled profile unsaveable and would reach every document type, not just working drafts.
- [x] ~~Does a comment change only its own recommendation?~~ — **Resolved: yes, card-scoped.** It informs that card's rewrite and is available to the Copilot. A lasting rule is recorded in the guardrails by Aisyah, deliberately.
- [x] ~~Should a comment be re-interpreted into a standing guardrail automatically?~~ — **Resolved: no.** Verbatim appending would fill the box with fragments that only make sense beside their card ("Different concepts" is not a rule). Re-wording them with a model means the model authors the rules it then follows, and the specific failure mode is over-generalisation — "HKMA's TSP is not our TPSP" becoming "do not compare terminology against HKMA", suppressing good recommendations invisibly. Aisyah keeps authorship; the trade-off, accepted deliberately, is that a correction is only permanent if she records it.
- [x] ~~Does commenting trigger a rewrite automatically?~~ — **Resolved: no, rewriting is a separate action.** Aisyah may leave several comments and rewrite once, or record a caveat with no rewrite at all. Automatic rewriting would spend a model call on every stray note and rewrite a card out from under her.
- [x] ~~Should the state that steers the engine be visible and editable?~~ — **Resolved: yes — the guardrails box.** State that changes what the tool writes must be state the drafter can read and change.
- [x] ~~Should the guardrails and the Playbook be one surface or two?~~ — **Resolved: two.** They steer different engines and are read at different moments. Each sits next to the thing it configures: guardrails on the card that generates from them, the Playbook beside the Copilot it conditions.
- [x] ~~What scope do the guardrails and the Playbook have?~~ — **Resolved: per workstream, both.** Institution-wide would let an Open Finance rule silently govern a technology-risk draft; per-draft would mean re-teaching the same lesson on every document beside it.
- [x] ~~What happens to the Source card and the Reviewed tab?~~ — **Resolved: both deleted.** The page header already shows the draft's owner, format and status, and the Reviewed tab duplicated the task screen. What the Reviewed tab uniquely offered — sight of accepted findings while drafting — is replaced by recommendations that cite their clauses in full, plus the not-yet-reflected section that names every accepted finding no recommendation drew on.
- [x] ~~Should a recommendation be insertable into the draft, or handed to the Copilot directly?~~ — **Resolved: neither.** Everything that reaches the page arrives through the Copilot conversation, where it is reviewed. A hand-off button would be a second route to the same place with weaker review.
- [x] ~~Is coverage measured against all recommendations, or only bookmarked ones?~~ — **Resolved: all generated recommendations**, consistently on both surfaces, so the number means the same thing wherever it is read.
- [ ] **Is there an upper bound on how many recommendations one generation may produce?** — **Deferred (non-blocking).** The count is free-form by design, and thirty accepted findings across five dimensions is not expected to produce an unreadable list. If it does, a cap is a small change and the card already scrolls within a fixed height, as the Pairwise findings box does.
- [ ] **Should a recommendation be dismissable, as a finding is?** — **Deferred (non-blocking).** Today the alternative to bookmarking is regenerating, which discards it. An explicit dismissal that survives regeneration would be a fourth state to design and is not needed to complete the journey.
- [ ] **Should an accepted finding be markable as needing no policy action?** — **Deferred (non-blocking).** It would let Aisyah clear the not-yet-reflected count deliberately rather than leaving it as a standing figure, but it is a fourth review state on a finding and the read-only section works without it.
- [ ] **Should the tool prompt her to record a comment as a guardrail?** — **Deferred (non-blocking).** A prompt after commenting — "make this a standing rule?", opening the guardrails pre-filled with her own words, unedited — would close the gap between noticing and recording without a model re-wording anything. Worth revisiting if corrections are observed recurring in practice.
- [ ] **Should the `/draft` template upload be made to work?** — **Deferred (non-blocking).** The affordance is mocked for the demo and nothing is stored or parsed. Text configuration covers the demo; a real upload needs parsing, storage and failure states.

---

## Appendix A — The reviewer's assessment

Nine AI-generated recommendations against the Open Finance Exposure Draft, scored 1–5 for usefulness by a BNM policy officer, with their written comments. This is the source of the five default guardrails and of the decision not to carry a type or a score. Reproduced from `archive/recommendations.xlsx`.

| #   | Type given | Recommendation                                                                  | Score | What the reviewer said                                                                                                                                                                                                                                                  |
| --- | ---------- | ------------------------------------------------------------------------------- | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 7   | Strategic  | Monitor voluntary-jurisdiction experience to calibrate phase sequencing         | **5** | "Valid recommendation"                                                                                                                                                                                                                                                  |
| 3   | Strength   | Maintain and promote the draft's consent infrastructure as a regional benchmark | 4     | "This is valid strength"                                                                                                                                                                                                                                                |
| 5   | Divergence | Strengthen the phased implementation timeline with concrete milestones          | 4     | Valid — but milestones were **deliberately** left unprescribed, because the platform operator is already working the detailed plan with pilot banks, and BNM policy documents are principle-based where possible                                                        |
| 8   | Strength   | Convert the financial-literacy encouragement into a requirement                 | 4     | "Valid recommendation" — but "I don't know if this can be considered as Strength, seems more like a Gap"                                                                                                                                                                |
| 9   | Strength   | Foundational design validated — no changes required on core alignment           | 4     | Fairly accurate, but the international standard "does not actually provide much detail" and the draft is "relatively high-level" too, so the apparent match is **the absence of detail on both sides**. Readers could wrongly infer strong alignment                    |
| 1   | Gap        | Add a public service-provider registry and anti-impersonation requirement       | 3     | Relevant in principle — but the peer regulator's "TSP" and ours are **different things**: theirs is closer to our _data consumer_, ours is an operational vendor                                                                                                        |
| 2   | Gap        | Extend data-sharing obligations to non-bank and big-tech players                | 3     | "The recommendation is good, but ED currently only covers banking participants" — so the asymmetry described **does not apply**                                                                                                                                         |
| 6   | Divergence | Reconcile the breach-response regime with the technology risk regime            | 3     | Possibly valid for further consideration — but the two documents are **owned by different departments**, and a third document already covers breach reporting                                                                                                           |
| 4   | Gap        | Clarify which technology-risk requirements apply to open finance participants   | **1** | BNM policy documents reference each other **in general terms by design**, "because the provision numbering may change when those documents are updated. To avoid the OF ED becoming outdated, it is intentional that we do not map requirements to specific provisions" |

**What this tells us.** Seven of nine scored 3 or above, so the underlying approach works. The failures are not randomness — they are four specific, repeatable mistakes (rows 4, 2, 1, 9), which become guardrails 1–4. Rows 5 and 6 are a different case: both were _reasonable_ and still partly wrong, because the reviewer held context that exists in no document. No guardrail can fix that, which is why every recommendation states its unverified assumptions instead of writing past them — and why the guardrails box is editable, so that when the drafter does supply the missing context, she has somewhere to put it.

---

## Epic-Level Technical Notes

Per-story API design, data models, implementation plans and test scenarios live in the five story specs. This section holds only what spans them.

### The Copilot is a scripted demo, and that is accepted

`frontend/src/features/drafting-workspace/CopilotChat.tsx` implements the five stages as **client-side scripted lifecycles** over `copilotV2Data.ts` — its own docstring says _"A static, scripted demo (no live model)"_. `streamCopilotMessage` exists in `frontend/src/lib/api.ts:418` but no component calls it; only the MSW handlers reference it. The engine's `copilot_reply` / `copilot_reply_stream` / `_system_prompt` are genuinely live and injected as seams, but the V2 UI does not use them.

The Playbook story therefore builds **both** paths deliberately: the engine's system-prompt injection (real, asserted against a recorded prompt) and the scripted stages visibly naming the section they follow (what the demo runs). Neither mocks the other. Recorded here so nobody reads "the Copilot follows my Playbook" as live prompting today. See that story's reality note for detail.

### Ownership map

| Surface                            | Owning story                              | Consumer                                     |
| ---------------------------------- | ----------------------------------------- | -------------------------------------------- |
| `{ws}/recommendations/{node}.json` | Recommendations from my accepted findings | Task screen + draft tab                      |
| `{ws}/guardrails.json`             | Recommendations from my accepted findings | Recommendations prompt only                  |
| `{ws}/playbook.json`               | A Playbook that configures the Copilot    | Copilot system prompt + scripted stages only |
| `{ws}/metadata/{node}.json`        | One name for the regulatory profile store | Node detail, and `parse_dimensions`          |

**Neither configuration file reads the other**, and neither is read by pairwise analysis. Separate modules, separate routes, separate prompts.

### Shared route inventory

| Route                                                  | Story                            | Notes                                                   |
| ------------------------------------------------------ | -------------------------------- | ------------------------------------------------------- |
| `GET …/tasks/{node}/recommendations`                   | 1                                | Never 404s on "not generated"                           |
| `POST …/tasks/{node}/recommendations/generate`         | 1                                | Two 409 gates before the model seam                     |
| `GET`/`PUT …/guardrails`                               | 1                                | Serves five defaults when absent, without writing       |
| `PATCH …/tasks/{node}/recommendations/{rec_id}`        | 2 (`bookmarked`) + 3 (`comment`) | **One handler, two stories** — see the merge note below |
| `POST …/tasks/{node}/recommendations/{rec_id}/rewrite` | 3                                | Evidence floor applies; original kept on failure        |
| `GET`/`PUT …/playbook`                                 | 4                                | Four sections; no `explore_task` key                    |
| `POST …/tasks/{node}/copilot`, `/copilot/stream`       | 4                                | Gain an optional `stage`; additive                      |

**The one shared handler.** Stories 2 and 3 both extend the `PATCH` route. Whichever lands first creates it with its own field and rejects the other with `400 INVALID_PATCH`; the second adds its field. This is the epic's only file-level contention, and it is why those two stories are "independent of each other" for design but not for merge order.

### Model seams and CI

- `generate_recommendations_fn` on `create_app` — one seam serving both generation and rewrite, mirroring `run_arm_g_fn` (`engine/api.py:593`).
- Every test injects a stub, so **CI needs no model or credentials**, the discipline `test_api_arm_g.py` and `test_copilot.py` already follow.
- The running service does reach a model on `generate` and `rewrite`. The demo runs from committed pre-generated output.
- **No new dependency in either `pyproject.toml` or `frontend/package.json`.** If that changes, `docs/learnings/pattern-engine-deps-live-in-two-places.md` applies — a new engine dep must be added to the project file _and_ the explicit `pip install` list in `.github/workflows/test.yml`, or CI fails collection on every `engine.api` importer while the local suite stays green.

### Files deleted by this epic

| File                                                          | Story | Why                                     |
| ------------------------------------------------------------- | ----- | --------------------------------------- |
| `frontend/src/features/task/SourceCard.tsx`                   | 1     | Duplicates the page header              |
| `frontend/src/features/drafting-workspace/LinkageRefCard.tsx` | 4     | Unreferenced once the Reviewed tab goes |
| `frontend/e2e/reviewed-tab.spec.ts`                           | 4     | Covers a tab that no longer exists      |
| `engine/concepts.py`                                          | 5     | `git mv` to `engine/node_metadata.py`   |

**`engine/api.py:2095` (`get_reviewed_linkages`) is NOT deleted.** It stops backing a tab and becomes the recommendation engine's evidence input — the same accepted-findings-across-the-neighbourhood set, read server-side instead of rendered.

### Cross-story build order

```
Story 5 (rename)  ─┐
                   ├→ Story 1 (recommendations + guardrails) ─┬→ Story 2 (bookmark) ─┐
Story 4 (playbook)─┘                                          └→ Story 3 (comment)  ─┴→ done
```

Story 5 first so Story 1's code is written against `metadata/` once. Story 4 is fully independent and can run in parallel from the start; it owns the tab replacement, so Story 2's three-tab assumption depends on it having landed (if Story 2 lands first, it leaves `reviewed` in place as a fourth tab rather than breaking the panel). Stories 2 and 3 share the `PATCH` handler — sequence them, either order.

### Repo conventions that apply throughout

- **UTF-8 on every write** of document or clause text (`encoding="utf-8"`) — `docs/learnings/pattern-engine-artifact-writes-utf8.md`.
- **Run builds in the main working tree**, not a worktree — `.venv` and `frontend/node_modules` exist only there (`docs/learnings/blocker-forge-build-run-in-main-worktree.md`).
- **The forge `stop-verify` hook false-fails here** with a cosmetic `LINT FAIL`; verify with `.venv/bin/python -m pytest engine/tests` (`docs/learnings/blocker-forge-verify-hook-false-fail-pyenv-ruff.md`).
- **Do not rebuild `data/artifacts/`** — a rebuild without Azure Document Intelligence silently narrows the clause index (`docs/learnings/blocker-engine-build-silently-narrows-artifacts.md`). Nothing in this epic needs it: everything reads `data/workstreams/`.
- **Retired fixtures are read-only.** No `metadata/`, `guardrails.json`, `playbook.json` or `recommendations/` is created for `opres-v2`, `rmit-v2-2025` or `open-finance-ed`. `git status --porcelain data/workstreams/` must be empty after a full suite run.
- **Nothing sensitive in a tracked path.** `data/workstreams/` is public: the demo `playbook.json`'s `deliver` section uses role names ("Head of Department, CMC"), never a personal email address.

### Demo seed data — the blocking prerequisite

| File                                                                                 | Contents                                                                                                                                                      |
| ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `data/workstreams/open-finance-pd-2026/metadata/open-finance-pd-2026-pd.json`        | The working draft's seven-field profile, with a real `policy_requirement` list. **Without this, generation is gated and the feature cannot be demonstrated.** |
| `data/workstreams/open-finance-pd-2026/recommendations/open-finance-pd-2026-pd.json` | A pre-generated set, so the demo needs no model call                                                                                                          |
| `data/workstreams/open-finance-pd-2026/playbook.json`                                | Four populated sections, role names only                                                                                                                      |
| `data/workstreams/open-finance-pd-2026/guardrails.json`                              | Optional — an absent file serves the five defaults, which is the better demo (it shows what ships)                                                            |

The one open item is **what the policy requirements should say**. They must be real Open Finance dimensions, and they determine what the pre-generated set contains.

### Spec-linter note

`scripts/validate-spec.sh` reports `story spec missing 'As a … I want … so that'` on every story file here. Its pattern requires a literal `As a`; this repo's house style names the persona (`As Aisyah R., I want …`), which every existing spec under `docs/specs/workstream-brain/` also uses — the same check fails on `spec-editable-node-metadata.md` today. The persona form is kept deliberately; the linter's other checks (placeholders, INDEPENDENT/SEQUENTIAL labels, Story Index entries) all pass.
