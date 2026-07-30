# Task Type & Editable Node Metadata — Overview

**Ticket:** None — this repo has no issue tracker (see `CLAUDE.md`)

## Summary

Every document in a workstream gains a complete, drafter-maintained regulatory identity. A working draft declares what kind of deliverable it is — a Policy Document, an FAQ, an Engagement Deck — once, at the moment it is created, from a single vocabulary the whole tool shares. Every document's regulatory profile becomes something Aisyah can fill in and correct herself, rather than a card that apologises for being empty. And because the tool now records what the drafter is working on, the Copilot stops asking.

## Background & Context

**Current state:**

- When Aisyah spins up a new workstream, she picks a deliverable kind from a four-option list: Policy Document, Exposure Draft, Discussion Paper, or Other. The working draft is named after her choice, so a new Open Finance response is titled "Open Finance ED response (ED)".
- When she adds any other document to the graph — a Basel standard, the Financial Services Act, a peer regulator's guideline — she classifies it structurally (is it an international standard? an act or law? industry input?) but nothing records what kind of deliverable it is.
- Each document has a Regulatory profile card showing nine fields: policy owner, applicability, empowerment framework, requirement, issuance date, effective date, keywords, legal basis, and ISMP classification. The card is read-only. Its contents were prepared ahead of time for a handful of documents; every other document shows a placeholder saying concept extraction is not enabled.
- When Aisyah opens the Copilot on a working draft, the first thing she meets is a dropdown asking what kind of deliverable she is producing. It offers seven options — Policy Document, Discussion Paper, Exposure Draft, FAQ, Engagement Deck, Feedback Template for Industry, Peer Benchmarking — and always starts on Policy Document, no matter what the draft actually is.

**Problem:**

- **The tool asks Aisyah a question it should already know the answer to.** She told it she was drafting an Exposure Draft when she created the workstream. The Copilot then greets her with a dropdown defaulted to Policy Document and expects her to answer again, every session. If she forgets, the Copilot frames its help for the wrong kind of document.
- **Two vocabularies describe the same thing and disagree.** Workstream creation offers four options; the Copilot offers seven. FAQs, engagement decks, feedback templates, and peer benchmarking exercises are real BNM deliverables the Copilot recognises but the workstream form cannot express, so a drafter producing an FAQ has to record it as "Other".
- **A document's regulatory profile is not something a drafter can maintain.** For most documents the card is empty and stays empty, because filling it in was a preparation step performed outside the tool. A drafter who spots a wrong policy owner, or knows the effective date the card is missing, has nowhere to put that knowledge.
- The consequence is a tool that looks like a demo fixture rather than a living workstream — the opposite of the institutional-continuity story this product exists to tell.

## Goals

- Establish **one shared vocabulary of eight deliverable kinds**, used identically wherever the tool asks or displays what a document is.
- Record a working draft's deliverable kind **once, at creation**, and display it wherever the document appears.
- Let Aisyah **fill in and correct a document's regulatory profile herself**, on any document in any workstream, and have her edits persist.
- **Stop asking the drafter what they are drafting.**

## Non-Goals

- **Teaching the Copilot to reason over the nine profile fields.** This epic ensures the fields are captured and saved. What the Copilot then does with a document's policy owner, applicability, or legal basis is a separate spec, deliberately not started here so that the Copilot's answering behaviour stays untouched before the demo.
- **Changing a deliverable kind after it is set.** The kind is chosen once and is thereafter a label. Renaming a working draft because its kind changed is out of scope, and the "Others" option exists so that an uncertain drafter still has a truthful answer.
- **Marking a profile field as "not applicable".** A field is either filled in or not set. A third state a drafter can choose is more form for very little value, and can follow later if drafters genuinely need it.
- **Deriving profile fields automatically from a document.** Populating the profile by reading the document is existing preparation work and is not extended here.
- **A deliverable kind for published context documents.** None of the eight kinds honestly describes the Basel Committee's operational resilience principles or the Financial Services Act 2013, so the field is not offered on them.

## Story Index

| Ticket | Story                                       | Spec                                                               | Type        | Status      | Dependencies          |
| ------ | ------------------------------------------- | ------------------------------------------------------------------ | ----------- | ----------- | --------------------- |
| None   | One shared vocabulary of deliverable kinds  | [spec-shared-task-type.md](spec-shared-task-type.md)               | User-facing | Not Started | —                     |
| None   | A regulatory profile the drafter can edit   | [spec-editable-node-metadata.md](spec-editable-node-metadata.md)   | User-facing | Not Started | —                     |
| None   | The Copilot stops asking what I am drafting | [spec-copilot-reads-task-type.md](spec-copilot-reads-task-type.md) | User-facing | Not Started | One shared vocabulary |

The first two stories are independent of each other and can be built in parallel. The third needs the first, because it works by reading the deliverable kind the first story records.

## Shared Business Rules

- **The vocabulary is exactly eight kinds**, and every place the tool asks or shows a deliverable kind uses this same list, in this order:

  | Shown to the drafter as        | Short form  |
  | ------------------------------ | ----------- |
  | PD — Policy Document           | `PD`        |
  | DP — Discussion Paper          | `DP`        |
  | ED — Exposure Draft            | `ED`        |
  | FAQ                            | `FAQ`       |
  | Engagement Deck                | `DECK`      |
  | Feedback Template for Industry | `FEEDBACK`  |
  | Peer Benchmarking              | `BENCHMARK` |
  | Others                         | `OTHERS`    |

- **The short form is what appears inside an automatically generated name.** When the tool names a working draft after the workstream, it uses the short form: "Climate Risk DP (DP)", "OpRes Industry Briefing (DECK)". A name Aisyah types herself is never altered.
- **A deliverable kind is required, and permanent.** Every working draft has one from the moment it exists, and it cannot be changed afterwards. "Others" is the honest answer when the drafter is not yet sure.
- **Only working drafts carry a deliverable kind.** Published context documents — international standards, acts and laws, peer regulator guidance, industry submissions, supervisory letters — do not, and are never asked for one.
- **The regulatory profile is drafter-authored context, not evidence.** Anything Aisyah types into a profile field is her own account of the document. It is never treated as a quotation from the document, and never presented as a citation. The tool's rule that every citation is quoted word-for-word from a source, with its clause number, is untouched by this epic.
- **A blank profile field means "not set yet."** It does not mean the field is inapplicable. The one exception is ISMP classification, which continues to read "Pending — RH publication form" because its source genuinely is not available to the tool, and saying so is more honest than showing a blank.
- **Every document can hold a profile.** The nine profile fields are offered on every document in every workstream, not only on working drafts.

## User Journey Map

1. **A new workstream is announced.** The Deputy Governor asks for an FAQ accompanying the RMiT policy document. Aisyah creates the workstream and picks "FAQ" from the deliverable list — a choice the tool could not previously express. The working draft appears on her canvas named "RMiT FAQ (FAQ)". _(Story: One shared vocabulary)_
2. **She builds out the graph.** She attaches the RMiT policy document, the Basel principles, and an industry submission. None of these asks her for a deliverable kind, because none of them is a deliverable she is producing. _(Story: One shared vocabulary)_
3. **She adds a second working draft.** Later in the cycle she adds an engagement deck to the same workstream. Because it is a working draft, the form asks what kind it is and will not let her continue until she says; she picks "Engagement Deck". _(Story: One shared vocabulary)_
4. **She inspects a document.** Opening the RMiT policy document, she sees its Regulatory profile. The policy owner is recorded but the effective date is missing, and she knows it: 28 November 2025. She presses Edit, types it in, and saves. The card shows it from then on. _(Story: A regulatory profile the drafter can edit)_
5. **She corrects a document nobody prepared.** The Basel principles document shows every profile field as not set. She fills in the two she is confident about — its keywords and its legal basis — and leaves the rest alone. _(Story: A regulatory profile the drafter can edit)_
6. **She starts drafting.** She opens the Copilot on the RMiT FAQ. It does not ask her what she is drafting. She types her first question and gets an answer straight away. _(Story: The Copilot stops asking what I am drafting)_

## Success Metrics

- **The drafter is never asked what they are drafting.** Opening the Copilot on any working draft goes straight to work, with no deliverable-kind question anywhere in the panel. This is the epic's single measure of success: the question that used to be asked every session is asked exactly once, when the draft is created, and never again.

## Dependencies

- **One existing workstream must be backfilled: the 2026 Open Finance policy document.** Its working draft is the one pre-existing draft the demo keeps, so it needs its deliverable kind recorded. Every other working draft that predates this field is being retired and needs nothing.
- **No new external systems.** ISMP classification remains unavailable to the tool and continues to display as pending; nothing in this epic depends on obtaining it.

## Rollout Strategy

All three stories land together for the 3 August demo. Suggested build order:

1. **One shared vocabulary** first, since it replaces both existing lists and the third story reads what it records.
2. **A regulatory profile the drafter can edit** in parallel with the first — the two do not touch each other, beyond the profile card also displaying the deliverable kind as a read-only line.
3. **The Copilot stops asking** last and quickly, once the deliverable kind is reliably recorded on every working draft.

No phased release or communication plan applies: this is a hackathon prototype with a single drafter persona and no external users.

---

## Dependencies & Integration

- **Affected features:** the graph screen's add-node dialog and node-detail panel, the new-workstream form, the drafting workspace's Copilot panel, and — indirectly — the Cross-Workstream Intelligence panel and comparison view, which project the same nine profile fields they have always read.
- **Shared state:** `data/workstreams/{ws}/graph.json` (nodes gain `task_type`) and `data/workstreams/{ws}/concepts/{node_id}.json` (the nine-field profile, now writable in-app as well as by the offline enrichment script).
- **Breaking changes:** two, both internal to this repo. `deliverable_type: "Other"` is no longer accepted by workstream creation, and `intent` is removed from both Copilot request bodies. The only clients are this app's own API layer and the test suite; no external consumer exists.
- **Migration path:** one fixture is backfilled by hand — `data/workstreams/open-finance-pd-2026/graph.json` gains `"task_type": "PD"` on its working draft. No other data changes.

## Shared Data Model

Two files under `data/workstreams/` change shape. There is no database.

**Graph node** (`{ws}/graph.json` → `nodes[]`) — one new key:

| Field       | Type             | Constraints                                            | Description                                        |
| ----------- | ---------------- | ------------------------------------------------------ | -------------------------------------------------- |
| `task_type` | string \| absent | One of the 8 codes. Present iff `node_type == "task"`. | The deliverable kind. Written once, never updated. |

**Regulatory profile** (`{ws}/concepts/{node_id}.json`) — shape unchanged, exactly the nine `CONCEPT_FIELDS`. Previously written only by `scripts/enrich_node_metadata.py`; now also by the app. `task_type` deliberately does **not** join this file: the profile is mutable and per-document, the deliverable kind is structural and permanent, so each has one home.

## Shared Architecture Notes

- **One vocabulary, one definition.** `TASK_TYPES` in `engine/workstreams.py` is the single ordered code→label map, mirrored as `TASK_TYPE_OPTIONS` in `frontend/src/lib/types.ts`. It replaces `DELIVERABLE_TYPES` (engine) and both `INTENTS` (engine) and `DELIVERABLE_TYPE_OPTIONS` / `COPILOT_INTENTS` / `COPILOT_INTENT_LABELS` (frontend). Those five names are deleted, not aliased — an alias is how two vocabularies drifted apart in the first place.
- **The existing label/code split is preserved.** `workstream.json` continues to store the human label (`"Policy Document"`), because `list_workstreams` projects it straight to the sidebar; graph nodes store the code (`"PD"`), because the title suffix and the detail badge derive from it. Story 3's fallback reverse-maps label → code from `TASK_TYPES` rather than a hand-written second map.
- **Merge order is flexible.** Stories 1 and 2 touch disjoint code. Story 1 deletes `copilot.INTENTS` while story 3 removes the request field that validated against it, so story 1 must repoint `_parse_copilot_request` at `TASK_TYPES` in the same change — after which either merge order leaves the suite green.
- **No new dependencies anywhere in the epic.** No form library, no date picker, no validation library. Both new forms use plain controlled state and native inputs, matching the deliberate decision recorded in `NewWorkstreamPage.tsx`'s docstring.
- **CI needs no model or credentials.** The one new route (metadata save) is pure filesystem, and the Copilot routes' model calls remain injected seams that every test stubs.
- **Two repo conventions this epic must respect:** a new engine dependency would have to be added to both `pyproject.toml` and the explicit `pip install` list in `.github/workflows/test.yml` (this epic adds none), and every `write_text` of document text passes `encoding="utf-8"` — `save_concepts` already does.

## Open Questions

- [x] ~~Should the eight kinds be one shared list, or should workstream creation and the Copilot keep separate lists?~~ — **Resolved:** one shared list of eight, replacing both. The current four-option and seven-option lists describe the same idea and disagree, which is what forces an FAQ to be recorded as "Other".
- [x] ~~Do the longer kinds need a short form?~~ — **Resolved:** yes. Automatically generated names embed the kind, and "OpRes Feedback (Feedback Template for Industry)" is unreadable where "OpRes Feedback (FEEDBACK)" is not.
- [x] ~~Can a drafter change a deliverable kind after choosing it?~~ — **Resolved:** no, fixed once chosen. This keeps automatically generated names correct forever without any renaming behaviour, and "Others" covers genuine uncertainty. Accepted trade-off: a drafter who picks "Others" early cannot refine it later.
- [x] ~~Is choosing a kind mandatory when adding a working draft?~~ — **Resolved:** mandatory. Because the choice is permanent, an optional field would produce working drafts that are blank forever — which is the problem this epic exists to remove.
- [x] ~~Do published context documents get a deliverable kind?~~ — **Resolved:** no. None of the eight kinds truthfully describes a Basel standard or an Act, so offering the field there invites a wrong answer.
- [x] ~~Should a drafter be able to mark a profile field as "not applicable"?~~ — **Resolved:** no. Blank means not set yet. The ISMP field keeps its existing "pending" wording because it has a specific, documented reason.
- [x] ~~May the Copilot quote a drafter-typed profile field as a citation?~~ — **Resolved:** no, never. Profile fields are the drafter's own account of a document and inform understanding only. The tool's word-for-word citation rule is unaffected.
- [ ] What the Copilot does with the nine profile fields once it can read them — **Deferred (non-blocking):** a separate spec owns this. This epic only guarantees the fields are captured and saved, so nothing here waits on that decision.
- [ ] Whether drafters need a way to mark how much of a profile is complete, across a whole workstream — **Deferred (non-blocking):** there is no baseline to measure against yet, and the demo does not depend on it.
