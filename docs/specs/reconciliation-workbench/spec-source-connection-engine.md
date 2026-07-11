# Two-Branch Source Connection Engine

**Ticket:** TBD
**Type:** Technical — Infrastructure / Platform

This is the core engine behind the Reconciliation Workbench. It ingests an uploaded
policy document, extracts its paragraphs, discovers the sources that bear on each
paragraph through two branches (sources the document already cites, and relevant
sources it did not cite), models every source as a first-class node with structural
metadata, connects each source to the paragraph(s) it touches, and proposes a verdict
(Consensus / Conflict / Gap / Duplicate / Partial) for every connection with the verbatim
supporting passage and a plain-language impact read. Every UI story in the epic reads
its paragraphs, connections, verdicts, quotes, and source metadata from this engine, so
nothing else in the Workbench can be built until this exists.

## Motivation

**Current state:** A policy drafter does due diligence by hand — scouring international
standards (OECD, NIST, BCBS), peer regulators (MAS, OSFI), national acts (the Personal
Data Protection Act), Bank Negara Malaysia's own policies, and industry feedback — to
work out which sources bear on each paragraph of an in-progress document and how the
draft stands against them. Each source lives somewhere different; the reconciliation
exists only in the drafter's memory, so the institution keeps no defensible,
clause-by-clause record of why the rulebook says what it says. There is no engine that
reads a document, links the scattered sources to its paragraphs, and proposes a
grounded verdict for each link. A naive attempt fails at the first step: the demo
vehicle — the _Discussion Paper on AI in the Malaysian Financial Sector_ (August 2025) —
is encoded with custom fonts, so plain text extraction returns gibberish rather than
its 54 numbered paragraphs.

**Desired state:** An uploaded document is ingested with high fidelity (the AI
Discussion Paper resolves to roughly 73,601 characters across 54 numbered paragraphs),
its own cited sources are parsed and classified, relevant un-cited sources are matched
from a curated library, every source is modelled as a typed node connected to the
specific paragraphs it bears on, and each connection carries a proposed verdict, the
verbatim supporting passage marked verified or illustrative, and a plain-language
impact read — all readable by the Workbench's UI stories through a stable read
interface.

**Trigger:** This is the first story in the epic's build order; every other story
(upload workspace, reconciliation and decision trail, cross-source insights, editable
grounded redraft assistant, drift monitor) depends on the data and verdicts this engine
produces. Discovery has cleared the riskiest assumptions — connection-finding with
verbatim citation and zero hallucination (Experiments A and B), citation parsing with
retrievability judgment (Experiment 4) — so the engine is a go-ahead to build. It must
exist before the 3 August 2026 hackathon demo.

## Scope

- **In scope:**
  - Ingest an uploaded policy document and extract its paragraphs and numbered
    structure with high fidelity, including documents encoded with custom fonts that
    defeat naive text extraction.
  - **Branch ① (cited sources):** parse the document's own footnotes and references,
    classify each cited source by source type, and judge which are retrievable versus
    not (for example, a Deputy Governor's speech or a forthcoming framework is not
    retrievable). For the demo, cited sources are catalogued and the source set is
    curated and clearly labelled.
  - **Branch ② (un-cited sources):** match the document's paragraph topics against a
    preloaded curated source library to surface relevant sources the document did not
    cite (the origin of gaps, conflicts, and missed connections). For the demo, the
    matched set is curated and clearly labelled.
  - Model every source as a first-class node carrying its source type and structural
    metadata (mother-document hierarchy, precedence / rank, whether it is legislated,
    the standard-setting party, and whether it is technical or principle-level).
  - Connect each source to the specific paragraph(s) it bears on.
  - For each connection, propose a verdict (Consensus / Conflict / Gap / Duplicate /
    Partial) with the verbatim supporting passage, a verification status marker, a
    plain-language impact read, and a rationale plus confidence — always a proposal, never
    a final call. Every proposal carries both its evidence (the verbatim passage) and its
    justification (the rationale), plus a **confidence band (High / Medium / Low)** — the
    same band the insights view uses. (How the band is derived is deferred to technical
    refinement.)
  - Return an explicit **"No matching source found"** result for a paragraph that has been
    analysed but has no source bearing on it — distinct from a paragraph that is not yet
    analysed.
  - Enforce the evidence-and-justification guardrail: emit "No matching clause found" when
    no passage supports a claim, and never fabricate a passage or assert a verdict without
    a rationale.
  - Provide the read interface and data the UI stories consume: paragraphs, connections,
    verdicts, quotes with verification status, source metadata, and per-connection
    rationale and confidence.

- **Out of scope:**
  - The upload UI and the reconciliation workspace surface (owned by _Upload &
    reconciliation workspace_).
  - The reconciliation act — pulling a principle in, anchoring to a rule, noting a gap,
    flagging a conflict — and the decision trail (owned by _Connection reconciliation &
    decision trail_).
  - Cross-source insights reasoning that spans multiple connections (owned by
    _Cross-source insights_).
  - The grounded redraft assistant and write-back of accepted changes to Word (owned by
    _Grounded redraft assistant & Word write-back_).
  - The drift monitor and prepared drift event (owned by _Source drift monitor_).
  - Confirming or overriding a proposed verdict — the engine proposes; a human commits
    through a later story.
  - **Live web retrieval / fetch of cited sources** — a documented production path,
    flagged as a residual build risk; the demo catalogues cited sources against a
    curated set.
  - **Topic-to-un-cited-source retrieval against a large source universe** — matching a
    paragraph's topic against the **preloaded curated library on demand** is in scope (it
    powers live "Analyse this paragraph"); retrieval at scale across a large, un-curated
    universe is unproven and flagged as a risk / roadmap item.

## Goals

- Extract the demo vehicle to roughly 73,601 characters across 54 numbered paragraphs,
  with paragraph numbers (for example 3.5, 3.11, 4.6) preserved and addressable — where
  naive extraction of the same custom-font document returns unreadable output.
- Parse and classify every cited source in the document by source type, and correctly
  separate retrievable published documents from non-retrievable items (speeches,
  forthcoming frameworks).
- Surface relevant un-cited sources from the curated library, connected to the correct
  paragraphs, with no invented equivalence (a connection the engine claims must genuinely
  bear on the paragraph's topic).
- Produce a proposed verdict, a verbatim supporting passage, a verification marker, an
  impact read, a rationale, and a confidence for every connection.
- Achieve zero unsupported claims: every connection, verdict, and impact read either
  quotes an existing passage verbatim or states "No matching clause found" — never
  fabricates.
- Expose all of the above through a stable read interface that the five downstream UI
  stories can build against without change.

## Non-Goals

- Building a continuously-running source watcher or live internet polling.
- Live parse-and-fetch of every cited source at demo time.
- A second full corpus beyond the one vehicle document plus one illustrative Basel row.
- Finalising any verdict or editing any policy text on the engine's own authority.
- Handling confidential sources with real content — confidential sources appear at most
  as a locked placeholder or a clearly-labelled mock, never with real content in a
  tracked path.

## Success Criteria

- Uploading the AI Discussion Paper yields its 54 numbered paragraphs as addressable
  units (3.5, 3.11, 4.6, and the rest), with the verbatim paragraph text readable
  through the read interface, and total extracted length in the region of 73,601
  characters.
- The engine fully analyses 8–10 paragraphs of the vehicle document — with 3.5, 3.11, and
  4.6 as the worked showcase paragraphs — returning for each connected source the correct
  source type, branch label (cited versus un-cited versus feedback), proposed verdict,
  verbatim quote with verification marker, impact read, and confidence value. Paragraphs
  not among the analysed set are addressable but carry no connections until analysed.
- Every quote the engine emits is marked either verified (checked word-for-word against
  the source) or illustrative (not yet verified), and no illustrative quote is ever
  presented as verified.
- Where no supporting passage exists for a claimed connection, the engine emits "No
  matching clause found" rather than a fabricated quote.
- A cited source that cannot be retrieved (for example, MAS FEAT, whose site blocks
  automated access) is returned as a labelled un-retrieved connection with a reason, not
  dropped and not fabricated.
- The read interface returns, for any paragraph, everything a downstream UI story needs
  to render the right rail, the connection detail, and the source-type legend without
  reaching past the engine.

## Acceptance Criteria

> Scenarios describe the engine's observable behaviour — the data it returns and the
> guarantees it makes — not its internal implementation. See `bdd-format.md` for the
> Gherkin rules.

### Scenario: High-fidelity extraction of a custom-font document

```gherkin
Given the AI Discussion Paper on Artificial Intelligence in the Malaysian Financial Sector is uploaded
  And the document is encoded with custom fonts that defeat naive text extraction
When the engine ingests the document
Then the engine returns roughly 73,601 characters of readable text
  And the engine returns 54 numbered paragraphs as addressable units
  And paragraph 3.5 reads "A major challenge of AI revolves around ensuring fair usage of the technology. AI models could exacerbate biases and discrimination, especially when the underlying input data is flawed or of low quality"
  And paragraph 4.6 is addressable by its number "4.6"
  And no paragraph text is unreadable gibberish
```

### Scenario: Naive extraction is rejected rather than passed downstream

```gherkin
Given a document whose extracted text is unreadable because of custom-font encoding
When the engine attempts to ingest it
Then the engine does not return gibberish paragraphs as if they were valid
  And the engine reports the document could not be extracted readably
  And no fabricated paragraph text is produced to fill the gap
```

### Scenario: Branch ① parses and classifies the document's own cited sources

```gherkin
Given the AI Discussion Paper has been extracted
When the engine parses the document's own footnotes and references
Then each cited source is returned with its organisation, year, and verbatim title
  And each cited source is classified by source type
  And the classification distinguishes the following

  | Cited source                          | Source type                        |
  | OECD AI Principles                     | international standard / principle |
  | BCBS 239                               | international standard / principle |
  | NIST AI Risk Management Framework      | international standard / principle |
  | MAS FEAT Principles                    | peer regulator                     |
```

### Scenario: Branch ① judges which cited sources are retrievable

```gherkin
Given the engine has parsed the document's cited sources
When the engine judges retrievability for each cited source
Then formally published documents are marked retrievable

  | Cited source                       | Retrievable |
  | BCBS 239                           | yes         |
  | NIST AI Risk Management Framework  | yes         |
  | a Deputy Governor's closing remarks| no          |
  | a forthcoming industry framework   | no          |
  And each non-retrievable source records the reason it cannot be retrieved
  And no non-retrievable source is dropped silently
```

### Scenario: A cited source that cannot be auto-retrieved is labelled, not fabricated

```gherkin
Given the engine has connected MAS FEAT Principles (Fairness) to paragraph 3.5 as a peer-regulator benchmark
  And the MAS source cannot be retrieved automatically because the site blocks automated access
When the engine returns the connection for paragraph 3.5
Then the connection is returned with an "could not retrieve" status
  And the connection records the reason the source could not be retrieved
  And the connection carries no verbatim quote
  And the connection is not assigned a fabricated passage or a confident verdict
```

### Scenario: Branch ② surfaces a relevant source the document did not cite

```gherkin
Given the AI Discussion Paper has been extracted
  And the curated source library holds the NIST AI Risk Management Framework
  And paragraph 3.5 concerns fair usage and bias
  And the document does not cite the NIST AI Risk Management Framework against paragraph 3.5
When the engine matches paragraph topics against the curated library
Then the engine returns a connection from the NIST AI Risk Management Framework to paragraph 3.5
  And the connection is labelled branch "un-cited — surfaced"
  And the connection carries the verbatim passage "Fairness and bias – as identified in the MAP function – are evaluated and results are documented."
  And the proposed verdict is "Gap"
  And the impact read explains that NIST makes fairness a measured, documented control that paragraph 3.5 states as an outcome but not as an evaluate-and-document obligation
```

### Scenario: Every connection carries a proposed verdict, a verbatim quote, an impact read, and a confidence

```gherkin
Given the engine has connected sources to paragraphs 3.5, 3.11, and 4.6
When a downstream story reads the connections for those paragraphs
Then each connection returns exactly one proposed verdict from Consensus, Conflict, Gap, Duplicate, or Partial
  And each connection returns the verbatim supporting passage with its clause or paragraph number
  And each connection returns a plain-language impact read of how the source affects the paragraph
  And each connection returns a rationale and a confidence for the proposed verdict
  And each verdict is marked as a proposal, never as a final decision
```

### Scenario Outline: The engine proposes the correct verdict for the demo connections

```gherkin
Given the engine has connected <source> to paragraph <paragraph>
When the engine proposes a verdict for the connection
Then the proposed verdict is <verdict>
  And the connection carries the verbatim passage <quote>

Examples:
  | paragraph | source                                  | verdict   | quote                                                                                                                                                                                 |
  | 3.5       | OECD AI Principles (1.2)                | Consensus | "AI actors should implement mechanisms and safeguards, such as capacity for human agency and oversight, including to address risks arising from uses outside of intended purpose."     |
  | 3.5       | BNM Fair Treatment of Financial Consumers (8.1) | Duplicate | "A financial service provider must ensure that financial consumers are treated fairly at all stages of their relationship with the financial service provider."                       |
  | 4.6       | PDPA 2010 as amended 2024 (§129)        | Conflict  | "A data controller may transfer any personal data of a data subject to any place outside Malaysia if— (a) there is in that place in force any law which is substantially similar to this Act"|
  | 4.6       | 3 FSP respondents (industry feedback, partial) | Partial | "The requirement to obtain informed consent is unworkable for models already trained on legacy datasets collected before AI use was contemplated."                                    |
```

### Scenario: A source that agrees in part and diverges in part is proposed as Partial

```gherkin
Given a source supports part of a paragraph's position and diverges on another part
  And industry feedback on the paragraph is categorised "partial"
When the engine proposes a verdict for the connection
Then the proposed verdict is "Partial"
  And the connection carries the verbatim passage evidencing both the agreement and the divergence
  And the rationale names which part aligns and which part diverges
```

### Scenario: An analysed paragraph with no bearing source returns "No matching source found"

```gherkin
Given a paragraph of the document has been analysed
  And no source in the curated library or the document's citations bears on it
When a downstream story reads that paragraph
Then the engine returns an explicit "No matching source found" result for the paragraph
  And this result is distinct from a paragraph that has not yet been analysed
  And no fabricated connection or quote is returned to fill the gap
```

### Scenario: The verbatim-citation guardrail blocks a claim with no supporting passage

```gherkin
Given the engine is evaluating a candidate connection between a source and a paragraph
  And no passage in the source supports a claim about the paragraph's topic
When the engine proposes a verdict for the candidate connection
Then the engine emits "No matching clause found"
  And the engine does not fabricate a supporting passage
  And the engine does not assert an unsupported verdict as though a passage backed it
```

### Scenario: Every quote is marked verified or illustrative

```gherkin
Given the engine has attached a verbatim passage to a connection
When the engine returns the connection
Then the quote is marked either "verified" or "illustrative"
  And a quote checked word-for-word against its source document is marked "verified"
  And a quote not yet checked against its source is marked "illustrative"
  And no illustrative quote is returned as verified
```

### Scenario: Industry feedback is analysed on the same engine as top-down sources

```gherkin
Given the curated library holds industry feedback on the published Discussion Paper
  And the Association of Banks submitted feedback agreeing with paragraph 3.11's treatment of GenAI hallucination risk
  And three financial service providers submitted feedback disagreeing with paragraph 4.6's informed-consent expectation
When the engine connects the feedback to the paragraphs it concerns
Then the Association of Banks feedback is connected to paragraph 3.11 with source type "industry feedback" and stance "agree"
  And the three-respondent feedback is connected to paragraph 4.6 with source type "industry feedback" and stance "disagree"
  And each feedback connection carries the verbatim comment and a proposed verdict on the same engine as any top-down source
```

### Scenario: Sources are modelled as first-class nodes with structural metadata

```gherkin
Given the engine has ingested the curated source library
When a downstream story reads a source node
Then the node returns its source type from international standard, peer regulator, act or law, internal BNM policy, or industry feedback
  And the node returns its structural metadata

  | Metadata                | Example value for PDPA 2010 (as amended 2024) |
  | mother-document         | Personal Data Protection Act 2010             |
  | precedence / rank       | national statute                              |
  | legislated              | yes                                           |
  | standard-setting party  | Parliament of Malaysia                        |
  | technical vs principle  | principle                                     |
  And each source node connects to the specific paragraph(s) it bears on
```

### Scenario: The read interface serves everything a downstream UI story needs for one paragraph

```gherkin
Given the engine has completed its analysis of the AI Discussion Paper
When a downstream story reads paragraph 3.5
Then the read interface returns the verbatim paragraph text
  And returns every connection for paragraph 3.5 with its source, source type, and branch label
  And returns each connection's proposed verdict, verbatim quote, verification marker, impact read, rationale, and confidence
  And returns any un-retrieved connection with its reason
  And the downstream story does not need any source of truth other than the engine to render the paragraph's connections
```

### Scenario: The engine surfaces the Gap-versus-Deviates nuance rather than forcing a blind call

```gherkin
Given a connection where one side adds an obligation the other side omits
  And the connection reads plausibly as both a Gap and a deliberate deviation
When the engine proposes a verdict for the connection
Then the engine proposes a single verdict with a confidence band of "Medium" or "Low" rather than "High"
  And the rationale notes that the connection could also be read as the alternative verdict
  And the proposal is marked for a human to confirm or override
```

### Scenario: The illustrative Basel row is returned as pending extraction, never approximated

```gherkin
Given the illustrative Basel row references the Basel III 72.5% output floor and Canada's OSFI output-floor freeze
  And those source documents are not yet available locally in verified form
When the engine returns the Basel row's connections
Then each affected connection is marked "pending extraction"
  And no approximated or paraphrased Basel or OSFI figure is returned as a verbatim quote
```

## Constraints

- **Backwards compatibility:** Must maintain the read interface's shape once the
  downstream UI stories begin building against it — paragraphs, connections, verdicts,
  quotes with verification status, and source metadata are a contract the workspace,
  reconciliation, insights, redraft assistant, and monitor stories all consume. Additive changes
  are acceptable; removing or renaming fields the UI stories rely on is a breaking
  change and must be coordinated.
- **Downtime:** Not applicable — this is a hackathon demo engine, not a live production
  service with an availability commitment. Reprocessing the vehicle document offline is
  acceptable.
- **Compliance:** The verbatim-citation guardrail is a hard requirement — every
  connection, verdict, and impact read quotes an existing passage verbatim or states
  "No matching clause found," and no passage is ever fabricated. The engine runs
  entirely on published, public documents; confidential sources are excluded and appear
  only as a locked placeholder or clearly-labelled mock, never with real content in a
  tracked path. Every quote carries a verified-versus-illustrative marker; an
  illustrative quote may never be presented as verified. The demo is honestly labelled:
  upload and extraction are real, while the cited-source set and the un-cited matched
  set are curated and pre-prepared.
- **Rollback:** Reversible. The engine produces read-only analysis over source
  documents and never mutates the vehicle draft or any source, so its output can be
  regenerated or discarded without side effects. Re-ingesting the vehicle document
  reproduces the analysis from scratch.

## Dependencies

- **Demo vehicle:** BNM's _Discussion Paper on Artificial Intelligence in the Malaysian
  Financial Sector_ (August 2025) — a real, citation-heavy document that extracts to
  roughly 73,601 characters across 54 numbered paragraphs, and requires a
  custom-font-capable ingestion step (naive extraction returns gibberish).
- **Curated source library (branch ②):** a preloaded set of public references matched to
  the vehicle's topics — OECD AI Principles, NIST AI Risk Management Framework, BCBS 239,
  the EU AI Act (Regulation 2024/1689), the Personal Data Protection Act 2010 (as amended
  2024), and the Fair Treatment of Financial Consumers policy — plus sample industry
  feedback. Maintaining this library is an ongoing operational task, not a per-upload one.
- **Illustrative Basel row:** the Basel III 72.5% output floor (BCBS d424 / Basel
  Framework RBC20) and Canada's OSFI output-floor freeze, carrying the IMF
  deviation-justification story. Both are public but not yet available locally in
  verified form; they must be sourced and extracted or shown as a labelled "pending
  extraction" placeholder — never an approximated quote.
- **Downstream stories:** every other story in the epic (upload workspace, reconciliation
  and decision trail, cross-source insights, grounded redraft assistant, drift monitor)
  reads from this engine's interface; those stories cannot begin until the interface is
  stable.

## Open Questions

- [x] ~~Which verdict vocabulary does the engine propose?~~ — **Resolved:** Consensus /
      Conflict / Gap / Duplicate, one per connection. The Gap-versus-Deviates ambiguity is
      handled by proposing a single verdict with a confidence and a rationale that surfaces
      the alternative reading; a human confirms or overrides through a later story.
- [x] ~~Does the engine finalise verdicts?~~ — **Resolved:** No. The engine proposes a
      verdict, a confidence, and a rationale; it never commits. Confirming or overriding is
      owned by the reconciliation story.
- [x] ~~Can the two owed Basel and OSFI citations be sourced and verified verbatim before
      the demo?~~ — **Resolved:** sourcing and extracting BCBS d424 / RBC20 and the OSFI
      freeze is a build task that will be attempted; the engine is **guaranteed** to return
      either the verbatim-verified passage or a labelled "pending extraction" marker — never
      an approximated quote. This affects the Basel row's content, not the engine's
      architecture.
- [ ] Live web retrieval of cited sources (branch ①) at demo time. — **Deferred
      (non-blocking):** parsing and retrievability judgment are proven; live fetch with
      allowlist retrieval, disambiguation, and human confirm is a documented production
      path and a residual build risk. For the demo, cited sources are catalogued against a
      curated set and clearly labelled.
- [ ] Topic-to-un-cited-source retrieval — how far does live on-demand matching scale?
      — **Partially resolved / risk flagged:** matching a paragraph's topic against the
      **preloaded curated library on demand is in scope** and powers live "Analyse this
      paragraph" for any of the 54 paragraphs (per the workspace story's decision). What
      remains unproven — and is flagged as the live-demo risk — is retrieval quality when the
      source universe grows large and un-curated; that scaling is a roadmap item. The
      verbatim-citation guardrail holds either way: no supporting passage → "No matching
      clause found," never an invented connection.

---

<!-- TECHNICAL SECTIONS (added by /prd-refine, 12 Jul 2026). Business content above
is unchanged. This extends the EXISTING engine/ (a real Python/FastAPI codebase),
reusing its proven parts and adding the new two-branch + verdict + reference-node work. -->

## Relationship to the existing engine (honest starting point)

A real `engine/` already exists and is green (see `engine/tests/`). It was built for the
prior pairwise design, so this story **reuses** a meaningful core and **adds** the rest.

**Reused as-is (proven, tested — do not rebuild):**

- `engine/ingest.py` — MarkItDown + optional Azure Document Intelligence conversion of
  PDF/DOCX → clean markdown, with the custom-font handling the vehicle needs, and
  `UnreadableDocumentError` for gibberish. Covers the "high-fidelity extraction" and
  "naive extraction rejected" criteria already.

> **✅ Prerequisite verified (12 Jul 2026).** The AI DP is already in the corpus
> (`data/corpus/dp_ai_financial_sector.pdf`, 699 KB) and extracts **cleanly** through this
> existing pipeline: **73,601 characters, 54 numbered paragraphs (1.1 … 5.10)**, with 3.5 /
> 3.11 / 4.6 present and readable. No new extractor is needed. (The earlier "79,666" figure
> was wrong and has been corrected to 73,601 throughout.)
>
> **✅ OCR glyph artifacts — RESOLVED (12 Jul 2026).** The default extraction rendered the
> DP's stylised "AI" logotype as "Al"/"$A l$"/"GenAl" in ~109 patterned spots (Azure
> Document Intelligence produced identical output — it did not help). Fixed by
> `engine.ingest.normalise_glyph_artifacts`, a **narrowly-scoped, tested** normaliser that
> repairs only the self-contained mangle patterns (short `$…$` "AI" wrappers, bare
> `Al`/`GenAl`/`Al-`/`Fls`) and provably leaves untouched: numeric math (`$(n=102)$`), real
> words ("Also", "Alert"), and long/unterminated `$…$` spans (a length guard prevents a
> dangling delimiter from swallowing the real paragraphs 4.8–5.10 / references table).
> Preserves trailing source punctuation (never drops a `.`/`,`). 12 tests in
> `engine/tests/test_ingest.py` cover the patterns, the safety cases, idempotency, and a
> real-PDF assertion that 3.5 / 3.11 come out clean. Because the PDF _says_ "AI" and the
> extractor broke it, this **strengthens** the verbatim guarantee. Build note: the DP's
> build path calls `normalise_glyph_artifacts` after `ingest_document`; it is **not** wired
> globally (the bare `Al`→`AI` fix is DP-specific and must not touch other corpus PDFs).

- `engine/clauses.py` — the anchor-slice segmenter (LLM finds boundaries; code slices
  verbatim text) and `ClauseIndex` (verbatim fetch by number). Reference passages already
  enter the index as single clauses (e.g. `"PDPA 129"`), per `build_reference_clause`.
- `engine/connections.py` — the finder → critic → **deterministic citation validator**
  loop. `_validate_candidates` is the anti-hallucination guardrail: a candidate is
  `supported` only when every cited clause resolves in the index, and its text is fetched
  verbatim by number — never model-produced. Unsupported candidates get
  `"No matching clause found"`. This is exactly the guardrail this story's criteria demand.
- `engine/graph.py` — nodes/edges with `kind`, `source_type`, `access`, `preview` already
  modelled for reference nodes (#26), plus the restricted/preview carve-out in the edge
  validator. The structural-metadata criterion builds directly on this.
- `engine/config.py` — `DOCUMENTS`, `REFERENCE_DOCUMENTS`, `CURATED_SEED_EDGES`,
  `REFERENCE_SEED_EDGES`, Azure deployment env wiring.
- `engine/api.py` — the injectable FastAPI factory `create_app(...)`; the read-route
  pattern and uniform `{error, message}` body are the template new routes follow.

**Net-new for this story (the spec-vs-code gap):**

1. **Verdict classification** — the current engine emits _raw_ clause-anchored connections
   and explicitly does **not** classify them (`connections.py` docstring). This story adds
   a verdict stage proposing one of **Consensus / Conflict / Gap / Duplicate / Partial**,
   each with a rationale and a **confidence band (High/Medium/Low)**.
2. **Two-branch orchestration** — cited-branch vs un-cited-branch as a first-class split
   over one uploaded document, replacing the "exactly two `document_ids`" pairwise call.
3. **Paragraph-level analysis over an uploaded document** — the vehicle DP as the analysed
   document, with an explicit **"No matching source found"** state for analysed-but-empty
   paragraphs.
4. **Un-retrieved (blocked) connection** shape (e.g. MAS FEAT) and the **pending-extraction**
   marker (Basel/OSFI) surfaced through the read API.
5. **`verified` vs `illustrative`** flag on every quote.

## Functional Requirements

- **Verdict is a proposal, never final.** Every connection carries `verdict`, `rationale`,
  `confidence` (`"High"|"Medium"|"Low"`) and `verdict_status: "proposed"`. The engine never
  emits a `"confirmed"` verdict — confirm/override is the reconciliation story.
- **Verbatim by construction.** A connection's `quote.text` is always fetched from
  `ClauseIndex.get(clause_number)["text"]` — never from the model. This is already true in
  `_cite(...)`; the verdict stage must not introduce a model-authored quote path.
- **Guardrail precedence.** Verdict classification runs **after** the citation validator.
  A candidate that fails validation is `unsupported` with `"No matching clause found"` and
  is **never** assigned a verdict — a verdict presupposes a resolved, verbatim citation.
- **Confidence derivation (resolved here, was deferred).** The band is computed
  deterministically from signals already present, not a second model round-trip:
  `High` when the seed/finder edge `confidence ≥ 0.85` **and** the critic did not attach a
  `scope_note`; `Medium` when `0.70 ≤ confidence < 0.85` **or** a `scope_note` is present;
  `Low` when `confidence < 0.70` **or** the verdict stage flags Gap-vs-Deviates ambiguity.
  A Gap-vs-Deviates-ambiguous connection is capped at `Medium`. (Thresholds live in
  `engine/verdicts.py` as named constants so they can be tuned without touching callers.)
  - **Honesty note (demo vs production).** In the demo the input `confidence` values are
    **frozen hand-set fixtures** (`engine/config.py`: MAS 0.88, PDPA 0.90, Basel 0.84 —
    the output of a one-off finder pass, frozen), so a demo band reflects a hand-set score,
    **not** a live model confidence. The demo and pitch must not claim otherwise. In
    production the **same formula** consumes real per-edge finder scores unchanged — the
    formula is the product; the fixtures are the demo stand-in. (This mirrors the existing
    `provenance: "llm-found"` + frozen-confidence pattern already in `config.py`.)
- **Idempotency.** Re-running analysis on the same document + same curated library +
  frozen finder fixtures yields byte-identical output (the build is already
  freeze-as-fixtures; the verdict stage must be pure given its inputs).
- **Analysed vs not-analysed.** A paragraph is "analysed" once the engine has run both
  branches (cited and un-cited) over it. The read API distinguishes three per-paragraph
  states: `analysed` with connections, `analysed` with `no_matching_source: true`, and
  `not_analysed` (never run).

## Permissions & Security

- All clause/graph/node/connection/paragraph routes are **public** — every byte derives
  from public BNM documents and public references (unchanged from `api.py`).
- The confidential handbook (`bnm-handbook`, `access: "restricted"`) and preview trend
  node remain **node-only**: no passage ingested, no text in any artifact. The verdict
  stage must skip restricted/preview reference targets (no verdict, no quote) — reuse the
  existing carve-out in `engine/graph.py`.
- No new write routes. The engine stays read-only over immutable build artifacts; nothing
  in this story mutates a draft or a source.
- Input validation on the new analyse route mirrors the existing pattern: unknown
  `document_id` / `paragraph_number` → `404`; malformed body → `400` with a specific code.

## API Design

New/changed routes on the existing `create_app(...)` factory. All responses use the
existing uniform error body `{"error": CODE, "message": "..."}`.

### `GET /documents/{document_id}/paragraphs`

Returns the uploaded document's paragraphs and their analysis state (drives the workspace
canvas + badges).

```json
{
  "document_id": "ai-dp-2025",
  "total_paragraphs": 54,
  "paragraphs": [
    {
      "number": "3.5",
      "title": "Fair usage & bias",
      "text": "A major challenge of AI…",
      "state": "analysed",
      "connection_count": 4
    },
    {
      "number": "4.6",
      "title": "Data & personal information",
      "text": "As AI applications…",
      "state": "analysed",
      "connection_count": 3
    },
    {
      "number": "3.2",
      "title": "Board & senior management oversight",
      "text": "The board and senior management…",
      "state": "not_analysed",
      "connection_count": 0
    }
  ]
}
```

### `GET /documents/{document_id}/paragraphs/{number}/connections`

Everything a downstream UI needs to render the right rail for one paragraph.

```json
{
  "paragraph": {
    "number": "4.6",
    "title": "Data & personal information",
    "text": "As AI applications…"
  },
  "state": "analysed",
  "no_matching_source": false,
  "connections": [
    {
      "id": "ai-dp-2025:4.6::pdpa-2010:PDPA 129",
      "branch": "uncited",
      "source": {
        "document_id": "pdpa-2010",
        "title": "Personal Data Protection Act 2010 (as amended 2024)",
        "source_type": "act"
      },
      "verdict": "Conflict",
      "verdict_status": "proposed",
      "confidence": "High",
      "rationale": "4.6 requires broad informed consent; PDPA §129 sets a specific cross-border transfer test the draft does not cite.",
      "quote": {
        "clause_number": "PDPA 129",
        "text": "A data controller may transfer any personal data of a data subject to any place outside Malaysia if— (a) there is in that place in force any law which is substantially similar to this Act…",
        "verification": "verified"
      }
    },
    {
      "id": "ai-dp-2025:4.6::industry-fsp-3",
      "branch": "feedback",
      "source": {
        "document_id": "industry-fsp-3",
        "title": "Industry feedback — 3 FSP respondents",
        "source_type": "industry_feedback",
        "stance": "partial"
      },
      "verdict": "Partial",
      "verdict_status": "proposed",
      "confidence": "Medium",
      "rationale": "Sector supports responsible data handling but rejects the informed-consent mechanism for legacy datasets — agrees in part, diverges in part.",
      "quote": {
        "clause_number": "Industry FSP-3",
        "text": "The requirement to obtain informed consent is unworkable for models already trained on legacy datasets collected before AI use was contemplated.",
        "verification": "illustrative"
      }
    }
  ]
}
```

An **un-retrieved** connection (blocked source) is shaped:

```json
{
  "id": "ai-dp-2025:3.5::mas-feat",
  "branch": "uncited",
  "source": {
    "document_id": "mas-feat",
    "title": "MAS — FEAT Principles (Fairness)",
    "source_type": "peer_regulator"
  },
  "status": "could_not_retrieve",
  "reason": "The MAS site blocks automated access; upload the source to analyse this connection.",
  "verdict": null,
  "quote": null
}
```

A **pending-extraction** connection (Basel/OSFI) carries `"quote": { "clause_number": "Basel RBC20", "text": null, "verification": "pending_extraction" }` — never an approximated string.

### `POST /documents/{document_id}/paragraphs/{number}/analyse`

Runs branch-① + branch-② for a not-yet-analysed paragraph on demand (powers live "Analyse
this paragraph"). Returns the same shape as the `GET …/connections` route. If nothing in
the curated library bears on the paragraph, returns `state: "analysed"`,
`no_matching_source: true`, `connections: []` — never a fabricated connection.

> **Architectural note — this is the ONE route that reaches the model at request time.**
> The rest of the read API stays deliberately model-free (analysis is build-time; the graph
> is held in memory). `POST /analyse` is the single opt-in exception: it invokes the
> finder + verdict seams live. To keep the demo's hero path safe:
>
> - **The 3 showcase paragraphs (3.5, 3.11, 4.6) are pre-analysed in the build artifacts**,
>   so the demo's core never depends on a live call. `GET …/connections` serves them
>   model-free.
> - **`POST /analyse` is only exercised for "analyse any _other_ paragraph"** — the live
>   wow-moment — and reuses the injectable `finder_fn`/`verdict_fn` seams, so tests stub it
>   (no network) exactly as `test_connections.py` already does.
> - **Fallback:** if the live call errors (Azure hiccup mid-pitch), the route returns a
>   graceful `503 ANALYSE_UNAVAILABLE` and the pre-baked paragraphs are unaffected —
>   mirroring the connection-trace backstop the engine already writes.

### Error table

| HTTP | Code                      | Message                                                                            |
| ---- | ------------------------- | ---------------------------------------------------------------------------------- |
| 404  | `DOCUMENT_NOT_FOUND`      | `No document with id '{id}'`                                                       |
| 404  | `PARAGRAPH_NOT_FOUND`     | `No paragraph '{number}' in document '{id}'`                                       |
| 400  | `INVALID_ANALYSE_REQUEST` | `Paragraph '{number}' is already analysed; re-analysis requires ?force=true`       |
| 409  | `SOURCE_LIBRARY_EMPTY`    | `No curated source library is loaded; cannot analyse`                              |
| 503  | `ANALYSE_UNAVAILABLE`     | `Live analysis is temporarily unavailable; pre-analysed paragraphs are unaffected` |
| 200  | (no error)                | `no_matching_source: true` is a success, not an error                              |

Existing routes (`GET /clauses/{n}`, `GET /graph`, `GET /nodes/{id}`) are unchanged and
must keep their current contracts.

## Data Model & Artifacts

No database. Two immutable JSON build artifacts (extended, not replaced):

**`data/artifacts/clause-index.json`** — unchanged shape; the vehicle DP's 54 paragraphs
enter as clause entries keyed `"{PolicyShortName} {number}"` (e.g. the DP as its own
`policy_id`), and reference passages continue to enter as single clauses.

**`data/artifacts/graph.json`** — reference nodes already carry `source_type`/`access`/
`preview`. Add, for reference/source nodes, the **structural metadata** the spec requires:

| Field                    | Type                         | Example (PDPA 2010)                   |
| ------------------------ | ---------------------------- | ------------------------------------- |
| `mother_document`        | string \| null               | `"Personal Data Protection Act 2010"` |
| `precedence`             | string                       | `"national statute"`                  |
| `legislated`             | bool                         | `true`                                |
| `standard_setting_party` | string                       | `"Parliament of Malaysia"`            |
| `doc_class`              | `"technical" \| "principle"` | `"principle"`                         |

**New: `data/artifacts/verdicts.json`** — per-connection verdict records (verdict,
rationale, confidence, branch, verification, source ref), keyed by the connection `id`
above. Written by the new verdict stage; the API joins it onto connections at read time.
`industry_feedback` sources and their stances (`agree|partial|disagree`) are added to
`REFERENCE_DOCUMENTS` in `engine/config.py`.

## Architecture Notes

- **New dependencies:** none. The verdict stage is another Azure-AI-Foundry call reusing
  `engine/llm.py` `call_chat` + `parse_json_response`, with the same injectable-seam
  discipline (`verdict_fn`) so tests need no network.
- **Integration points:** `engine/build.py` gains a stage-4b verdict pass after
  connection-finding; `engine/api.py` gains the three routes above via `create_app`. Two of
  the three (`GET …/paragraphs`, `GET …/connections`) stay model-free (served from build
  artifacts); only `POST …/analyse` reaches the model at request time, via the same
  injectable seams. Downstream UI stories read only through these routes.
- **Confidence is code, not a model call** (see Functional Requirements) — keeps the band
  deterministic and testable.

## Exemplar Files

- `engine/connections.py` — the finder→critic→validator loop + injectable seams + trace
  writing. The verdict stage mirrors this exactly: injectable `verdict_fn`, deterministic
  post-processing, recorded trace.
- `engine/tests/test_connections.py` — the no-network test pattern (stub both agent turns,
  hand-built `ClauseIndex`, tmp trace dir). New verdict/API tests follow it.
- `engine/api.py` `create_app(...)` + `engine/tests/test_api.py` — the factory + fixture
  pattern for the new routes.

## Implementation Plan

### Sub-tasks

**Task 1: Vehicle-document ingest + paragraph index for the AI DP** — _small_

- The DP source is **already present** (`data/corpus/dp_ai_financial_sector.pdf`) and
  extracts cleanly via the existing `engine/ingest.py` (verified: 73,601 chars, 54
  paragraphs). The glyph-normalisation step is **already built and tested**
  (`normalise_glyph_artifacts` + 12 tests — see the ✅ note above). Remaining work: add the
  DP's `DOCUMENTS` entry to `engine/config.py`, call `normalise_glyph_artifacts` on the
  DP's build path after `ingest_document`, and run the existing segmenter over it.
- Files: `engine/config.py`, `engine/build.py` (call the normaliser on the DP path),
  `engine/tests/test_build.py`
- SEQUENTIAL (foundation for everything below; ingest/segment/normalise already proven on
  this file)

**Task 2: Structural-metadata fields on source nodes** — _small_

- Add `mother_document`/`precedence`/`legislated`/`standard_setting_party`/`doc_class` to
  `REFERENCE_DOCUMENTS` and surface them through `engine/graph.py` node build.
- Files: `engine/config.py`, `engine/graph.py`, `engine/tests/test_graph.py`
- INDEPENDENT

**Task 3: `industry_feedback` source type + stance** — _small_

- Add feedback sources (AoB agree/3.11; 3-FSP partial/4.6) with `stance` to config; ensure
  the graph + edge validator accept them.
- Files: `engine/config.py`, `engine/graph.py`, `engine/tests/test_graph.py`
- INDEPENDENT

**Task 4: Verdict stage (`engine/verdicts.py`)** — _large_

- New module: given a validated `Connection`, propose `verdict` ∈ {Consensus, Conflict,
  Gap, Duplicate, Partial} + `rationale`, via injectable `verdict_fn` (Azure default,
  stubbed in tests). Deterministic confidence-band computation + Gap-vs-Deviates ambiguity
  cap. Never verdicts an `unsupported`/restricted/preview connection.
- Files: `engine/verdicts.py` (new), `engine/tests/test_verdicts.py` (new),
  `engine/build.py` (wire stage 4b), `data/artifacts/verdicts.json`
- SEQUENTIAL (depends on Task 1)

**Task 5: Two-branch orchestration over the uploaded document** — _large_

- Replace the "exactly two document_ids" call with branch-① (document's cited sources) +
  branch-② (topic-match against curated library) producing per-paragraph connection sets;
  emit the `no_matching_source` state; carry the `could_not_retrieve` and
  `pending_extraction` markers.
- Files: `engine/connections.py`, `engine/build.py`, `engine/tests/test_connections.py`
- SEQUENTIAL (depends on Tasks 1, 4)

**Task 6: Read API routes** — _medium_

- Add the three routes to `create_app`; join `verdicts.json` onto connections; preserve
  existing routes/contracts.
- Files: `engine/api.py`, `engine/tests/test_api.py`
- SEQUENTIAL (depends on Task 5)

### Negative Constraints

- Do NOT rewrite the finder→critic→**citation validator** guardrail in
  `engine/connections.py` — verdicts layer on top of validated connections.
- Do NOT remove or change the existing `GET /clauses`, `GET /graph`, `GET /nodes` contracts
  (they are green and may already have consumers).
- Do NOT touch `engine/submissions.py` or the supervisor routes — the supervisor persona is
  deferred; leave that code inert, don't delete it.
- Do NOT ingest any `access: "restricted"` reference text (the handbook). Node-only stays
  node-only.
- Do NOT let the verdict stage author quote text — quotes come from `ClauseIndex` only.

## Test Scenarios

**Test 1: Verdict stage proposes Conflict for 4.6 ↔ PDPA §129, quote fetched verbatim**

- Setup: `ClauseIndex` with DP 4.6 + `"PDPA 129"` (real passage from config); stub
  `verdict_fn` → `{"verdict": "Conflict", "rationale": "…cross-border transfer test…"}`.
- Action: run verdict stage on the validated connection.
- Expected: record has `verdict: "Conflict"`, `verdict_status: "proposed"`,
  `confidence: "High"`, and `quote.text` equals the index text byte-for-byte (not the
  stub's).

**Test 2: Partial verdict for the 3-FSP feedback on 4.6**

- Setup: feedback source `industry-fsp-3` stance `partial`; stub `verdict_fn` →
  `{"verdict": "Partial", "rationale": "agrees on responsible handling, rejects consent for legacy data"}`.
- Action: run verdict stage.
- Expected: `verdict: "Partial"`, `confidence: "Medium"`, `verification: "illustrative"`.

**Test 3: Gap-vs-Deviates ambiguity caps confidence at Medium**

- Setup: connection flagged ambiguous (finder confidence 0.9 but ambiguity flag set).
- Action: compute confidence band.
- Expected: `confidence == "Medium"` (not `High`), and `rationale` notes the alternative
  reading. (Guards the spec's "surfaces the nuance rather than a blind call" criterion.)

**Test 4: Unsupported candidate never gets a verdict**

- Setup: candidate citing `"Cyber 4.4"` (absent from index) — reuses the existing
  `test_connections.py` Test 7 fixture.
- Action: run validator then verdict stage.
- Expected: candidate is in `unsupported` with `"No matching clause found"`; `verdicts.json`
  has **no** record for it.

**Test 5: `POST …/analyse` on a bare paragraph returns no_matching_source, not a fabrication**

- Setup: app built with DP paragraph `3.2` (`not_analysed`) and a curated library with
  nothing on board-oversight; stub finder/verdict to return `[]`.
- Action: `POST /documents/ai-dp-2025/paragraphs/3.2/analyse`.
- Expected: `200`, `state: "analysed"`, `no_matching_source: true`, `connections: []`.

**Test 6: `GET …/connections` for 4.6 returns full render payload**

- Setup: built app with 4.6 analysed (PDPA Conflict + FSP Partial + BCBS 239 Consensus).
- Action: `GET /documents/ai-dp-2025/paragraphs/4.6/connections`.
- Expected: three connections, each with `branch`, `source.source_type`, `verdict`,
  `confidence`, `rationale`, and a `quote` with a `verification` marker.

**Test 7: Blocked source (MAS FEAT) surfaces as could_not_retrieve with no quote**

- Setup: config marks `mas-feat` connected to 3.5 but un-retrieved.
- Action: `GET …/3.5/connections`.
- Expected: the MAS connection has `status: "could_not_retrieve"`, a `reason`,
  `verdict: null`, `quote: null` — and no fabricated verdict.

**Test 8: Pending-extraction Basel row never emits an approximated quote**

- Setup: Basel/OSFI reference present but passage not extracted.
- Action: read its connection.
- Expected: `quote.text: null`, `verification: "pending_extraction"`; no non-null
  approximated string anywhere in the payload.

## Acceptance Criteria

- [ ] The AI DP ingests to ~73,601 chars / 54 addressable paragraphs via the existing
      MarkItDown+DI path (no new extractor).
- [ ] Verdict stage proposes exactly one of Consensus/Conflict/Gap/Duplicate/Partial per
      supported connection, with `verdict_status: "proposed"`, a rationale, and a
      High/Medium/Low confidence band computed in code.
- [ ] The citation validator still gates verdicts — no `unsupported` or restricted/preview
      connection ever carries a verdict or a quote.
- [ ] Every quote carries `verification ∈ {verified, illustrative, pending_extraction}`;
      no illustrative/pending quote is presented as verified.
- [ ] The three new API routes return the documented shapes; existing routes unchanged.
- [ ] `no_matching_source` and `could_not_retrieve` states are distinct from
      `not_analysed`, and none fabricates a connection.
- [ ] All existing `engine/tests/` pass; new tests for verdicts + routes pass.
- [ ] No new type errors beyond the accepted mypy stub baseline; ruff clean.

## Verification

Run the `verifier` skill (auto-detects Python/pytest) on changed files.

### Backend Tests

- `engine/tests/test_verdicts.py` (new) — Tests 1–4 above (verdict proposal, Partial,
  ambiguity cap, unsupported-gets-no-verdict).
- `engine/tests/test_connections.py` (extend) — Test 5 (analyse → no_matching_source),
  branch-① / branch-② orchestration, blocked + pending-extraction markers.
- `engine/tests/test_api.py` (extend) — Tests 6–8 (route payloads, blocked source,
  pending extraction) via the `create_app` fixture pattern; assert existing routes
  unchanged.
- `engine/tests/test_graph.py` (extend) — structural-metadata fields + industry_feedback
  nodes.

### Manual Verification

- [ ] `python -m engine.build` runs offline (deterministic stages) and writes
      `clause-index.json`, `graph.json`, `verdicts.json` without credentials.
- [ ] `uvicorn engine.api:app` starts on a fresh checkout (tolerates absent artifacts) and
      the three new routes return the documented shapes against the built artifacts.
- [ ] Spot-check that the DP 4.6 → PDPA §129 quote in the API response is byte-identical to
      the passage in `engine/config.py`.

_No E2E tests: this story has no user-facing UI — downstream UI stories own their E2E
coverage. Verdict/route behaviour is covered by the backend tests above._

## Open Questions (technical)

- [x] ~~How is the confidence band derived?~~ — **Resolved (this refinement):** computed
      in code from the finder/seed edge confidence + presence of a critic `scope_note` +
      the Gap-vs-Deviates ambiguity flag; thresholds are named constants in
      `engine/verdicts.py`. No second model round-trip. The same band feeds the insights
      story.
- [x] ~~Does verdict classification risk the verbatim guardrail?~~ — **Resolved:** no.
      Verdicts run strictly after the deterministic citation validator; quotes are always
      fetched from `ClauseIndex` by number, and an unsupported/restricted/preview
      connection is never verdicted.
- [ ] Should `verdicts.json` be a separate artifact or folded into `graph.json` edges? —
      **Deferred (non-blocking):** kept separate for now so the verdict stage can be
      re-run without rebuilding the graph; can be merged later if the API join proves
      awkward. Does not affect the route contracts.
- [ ] Exact `document_id` for the AI DP (`ai-dp-2025` is a working placeholder). —
      **Deferred (non-blocking):** naming only; settle when the DP source PDF lands in
      `data/corpus/`.
