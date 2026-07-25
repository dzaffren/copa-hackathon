# Wire Arm G Pipeline onto the Analyze Route

**Ticket:** TBD
**Type:** Technical — Performance / Migration

Replaces the current single-pass finding pipeline on the analyze route with the Arm G two-stage pipeline built in Story 2. The drafter's experience is unchanged — same findings, same response shape, same review workflow — but the engine now runs the smarter, cheaper pipeline that correctly separates same-topic findings from coverage findings under the hood.

## Motivation

**Current state:** The analyze route calls the existing single-pass pairwise finder for every document pair. That pipeline uses the most expensive available model for every step, making each run slow and costly. It also produces structurally unreliable coverage findings — because the finder only ever sees two anchors at a time, it cannot verify that a topic is genuinely absent from the other document as a whole. Policy drafters see coverage labels that are really mislabelled disagreements, which wastes review time and erodes trust in the tool.

**Desired state:** The analyze route calls the Arm G pipeline instead. The two-stage flow handles same-topic and coverage findings through separate, purpose-fit passes, routing each step to the right-sized model. Coverage findings that reach the drafter reflect genuine one-sided gaps, confirmed against the whole other document. Same-topic findings are unchanged in shape and quality. The axis cache — the topic-phrase index that makes retrieval possible — is populated automatically the first time a document pair is analyzed, so the drafter never has to run a separate preparation step.

**Trigger:** The Arm G experiment (validated across three document pairs — Open Finance ED × HKMA, × BIS Working Paper, × RMiT) proved the two-stage approach fixes all three problems — structural unreliability of coverage labels, slow runtimes, and excessive model cost. Story 2 builds that pipeline inside the engine. This story wires it onto the live route so the product benefits from the improvement.

## Scope

- **In scope:**
  - Replacing the pipeline the analyze route calls with the Arm G pipeline from Story 2.
  - Automatic axis cache population as part of an analysis run when the cache is missing for either document in the pair.
  - Writing each analysis result to a per-link location on disk (keyed by the two documents being compared) so that any link can be analyzed independently, and re-analyzing the same link cleanly replaces its previous result. No database — findings are files, consistent with how the rest of the engine stores state.
  - Supporting the demo flow of adding a new document to a workstream and immediately analyzing its links, with no separate setup step beyond the automatic axis extraction.
  - Reusing the existing injectable pipeline seam so tests can stub the Arm G pipeline the same way they currently stub the old finder.
  - Preserving the existing response shape exactly — same fields, same finding structure, same status values.
  - Verifying that pre-computed findings files stored on disk for existing workstream fixtures are unaffected.
  - Verifying that the accept/dismiss/flag review workflow continues to work without change.

- **Out of scope:**
  - Any change to what findings look like in the frontend — the output shape is identical to today.
  - Any change to the review or accept/dismiss workflow.
  - Building a cost or performance dashboard.
  - Supporting real-time streaming of findings as they arrive during a run.
  - Changes to the frontend or the Workstream Brain graph screen.

## Goals

- Analysis wall-clock time for a typical document pair (89 anchors × 127 anchors, such as the Open Finance ED × HKMA pair) drops below 90 seconds end-to-end.
- Cost per analysis run drops by at least 80% compared to the current single-model approach.
- Coverage findings in the response are structurally single-sided — every "silent on" and "goes beyond" finding is confirmed against the whole of the other document, not just a nearby anchor.
- Existing pre-computed fixture findings and the review workflow are completely unaffected.

## Non-Goals

- Changing what findings look like to the drafter in any way.
- Building any mechanism for the engine to analyze documents without a human triggering it.
- Introducing a cost reporting interface or per-run model-usage log visible to the drafter.
- Supporting streaming of partial findings as the pipeline runs.

## Success Criteria

- A triggered analysis of the Open Finance ED × HKMA pair completes end-to-end in under 90 seconds.
- The response for any analyzed pair contains findings with the same shape as today — every finding carries a label, verbatim clause text, and a clause number; the overall response carries the same status field and findings list.
- All coverage findings ("silent on" and "goes beyond") in the response are single-sided: each cites a clause from exactly one document, not both simultaneously.
- Pre-computed findings stored on disk for existing workstream fixtures are byte-for-byte unchanged after this story lands.
- The review workflow — accept, dismiss, flag for follow-up — continues to work on findings produced by the new pipeline without any frontend change.
- The injectable pipeline seam is honored: tests can substitute a stub for the Arm G pipeline, and the route behaves correctly with the stub in place.
- Each link's findings are stored at a per-link location; analyzing one link never overwrites another's result, and re-analyzing a link replaces only its own findings. Adding a new document and analyzing its links works with no manual preparation beyond automatic axis extraction — no database is introduced.

## Acceptance Criteria

### Background

```gherkin
Background:
  Given Aisyah is the policy drafter working in Workstream Brain
  And the Open Finance workstream contains a link between the Open Finance ED response and the HKMA Open API framework
  And the RMiT workstream contains a link between the OpRes PD v0.3 draft and the RMiT published standard
```

### Scenario: Analysis of a document pair returns findings through the Arm G pipeline

```gherkin
Given Aisyah opens the relationship between the Open Finance ED response and the HKMA Open API framework
  And neither document has been analyzed before
When Aisyah triggers analysis of this pair
Then the system runs the Arm G two-stage pipeline on the pair
  And returns a list of findings covering both same-topic and coverage relationships
  And every finding quotes the exact clause text it relies on, with its clause number
  And the response carries an "analysed" status and a count of findings returned
```

### Scenario: Response shape is identical to today

```gherkin
Given Aisyah triggers analysis of the Open Finance ED response against the HKMA Open API framework
When the analysis completes
Then each finding in the response carries a label from the five-label taxonomy
  And each finding carries verbatim clause text from the source document
  And each finding carries a clause number identifying where in the document it was found
  And same-topic findings (aligns-with, differs-on, conflicts-with) cite clauses from both documents
  And coverage findings (silent-on, goes-beyond) cite a clause from one document only
  And differs-on findings optionally carry a sentiment value of "tighten", "loosen", or "neutral"
  And coverage findings carry no sentiment value
```

### Scenario: Axis cache is populated automatically on first analysis

```gherkin
Given the topic-phrase index has never been built for the Open Finance ED response or the HKMA Open API framework
When Aisyah triggers analysis of this pair for the first time
Then the system builds the topic-phrase index for both documents as part of the analysis run
  And continues immediately to produce findings without requiring a separate manual step
  And the analysis completes and findings are returned to Aisyah as normal
```

### Scenario: Existing axis cache is reused without re-extraction

```gherkin
Given Aisyah has previously analyzed the Open Finance ED response against the HKMA Open API framework
  And the topic-phrase index for both documents is already on disk from that prior run
When Aisyah triggers analysis of the same pair again
Then the system reuses the existing topic-phrase index without rebuilding it
  And the second run completes faster than the first, since extraction is skipped
  And the findings returned are produced from the same topic-phrase data as before
```

### Scenario: The injectable pipeline seam works for test stubs

```gherkin
Given the analyze route is configured with a stub pipeline instead of the real Arm G pipeline
  And the stub is configured to return a fixed set of two findings for any input pair
When analysis is triggered on any document pair
Then the route calls the stub rather than the real pipeline
  And returns the stub's two findings in the standard response shape
  And the findings count in the response matches the stub's output
```

### Scenario: Pre-computed fixture findings are unaffected

```gherkin
Given the RMiT workstream has pre-computed findings already stored on disk for the OpRes PD v0.3 × RMiT link
  And no analysis is triggered on that pair
When the drafter opens the findings for that pair
Then the response contains the same pre-computed findings as before
  And none of those findings have been modified, re-labeled, or removed
  And the pair's "analysed" status and findings count are unchanged
```

### Scenario: Accepted and dismissed findings continue to work after the pipeline change

```gherkin
Given the drafter has previously analyzed the Open Finance ED × HKMA pair using the old pipeline
  And one finding was accepted and one finding was dismissed during review
When the drafter views the review state for that pair
Then the accepted finding still shows as accepted
  And the dismissed finding still shows as dismissed
  And the review workflow actions (accept, dismiss, flag) remain available on any unreviewed findings
```

### Scenario: Analysis of the Open Finance ED × HKMA pair completes within the time limit

```gherkin
Given the Open Finance ED response has 127 anchors
  And the HKMA Open API framework has 89 anchors
  And Aisyah triggers analysis of this pair
When the pipeline runs end-to-end including any axis extraction needed
Then the analysis completes and findings are returned within 90 seconds
```

### Scenario: Whole-document coverage pass failure surfaces as an error

```gherkin
Given Aisyah triggers analysis of the Open Finance ED response against the HKMA Open API framework
  And the large-model call for the whole-document coverage pass fails during the run
When the pipeline encounters the failure
Then the analyze route returns an error response
  And the error response does not contain any partial findings
  And no incomplete findings file is written to disk for the pair
  And the pair's analysed status remains as it was before the run started
```

### Scenario: Analysis is refused when a document in the pair has not been ingested

```gherkin
Given a workstream contains a link where one of the two documents has no ingested content
When Aisyah triggers analysis of that link
Then the route returns an informative error naming which side of the link is missing
  And no analysis is attempted
  And no findings file is written
```

### Scenario: Analysis run produces no findings

```gherkin
Given Aisyah triggers analysis of a document pair that the pipeline determines have no meaningful relationships
When the pipeline completes but produces zero supported findings
Then the route returns a "no linkages found" status
  And the findings list in the response is empty
  And no findings file is written to disk
  And the pair's analysed status remains unset, leaving it available for re-analysis
```

### Scenario: Re-analyzing a link replaces only that link's findings

```gherkin
Given Aisyah has already analyzed the Open Finance ED response against the HKMA Open API framework
  And that link's findings are stored on disk
  And a separate link in the same workstream also has stored findings
When Aisyah triggers analysis of the Open Finance ED × HKMA link again
Then the Open Finance ED × HKMA link's findings are replaced with the new run's results
  And the separate link's stored findings are left untouched
```

### Scenario: Adding a new document and analyzing its links needs no manual setup

```gherkin
Given Aisyah adds a new published document as a node in the Open Finance workstream
  And she creates a link between the new document and the Open Finance ED response
When Aisyah triggers analysis of that new link for the first time
Then the system extracts topic phrases for the new document as part of the run
  And produces findings for the new link
  And stores them at that link's own location without affecting any other link
  And no separate preparation step or database setup is required
```

### Scenario: Coverage findings are single-sided — no finding cites clauses from both documents simultaneously

```gherkin
Given analysis of the Open Finance ED × HKMA pair completes
  And the response contains both same-topic findings and coverage findings
When a policy drafter reviews each coverage finding
Then every "silent on" finding cites a clause only from the document that covers the topic
  And every "goes beyond" finding cites a clause only from the document that goes further
  And no coverage finding simultaneously cites clauses from both sides as its primary evidence
```

## Constraints

- **Backwards compatibility:** Must maintain fully. Existing pre-computed findings files on disk, the five-label taxonomy, the verbatim-citation guarantee, and the review workflow must all work exactly as before. No frontend changes are required or permitted.
- **Downtime:** Zero-downtime required. The route must continue to serve existing pre-computed findings throughout the change.
- **Compliance:** Every finding returned by the route must quote the exact clause it relies on, with its clause number. If no clause supports a claim, it must be flagged as unsupported and must not appear as a real finding to the drafter. This guarantee is unchanged by the pipeline swap.
- **Rollback:** Must be reversible. The injectable seam means the prior pipeline can be substituted back without any other change.

## Dependencies

- Story 2 (Arm G finding pipeline in the engine) must be complete before this story can be wired. The route swap has nothing to call until the pipeline exists inside the engine.
- Three model deployments must be available in the environment: a small model for topic-phrase extraction, a mid-tier model for per-pair same-topic judgment, and a large model for whole-document coverage reasoning. These are configured in Story 1 (three-tier model configuration).
- An embeddings endpoint is preferred (enables cosine retrieval, the validated default) but not required — if it is absent, the pipeline automatically falls back to BM25 keyword retrieval, so analysis can still run.
- The anchor index must contain entries for both documents in the pair being analyzed, covering the full clause text needed for verbatim citation.

## Open Questions

- [x] ~~Should the axis cache be stored alongside the anchor index or in a separate cache directory?~~ — **Resolved (deferred to Story 1/2 implementation):** Either location works; the pipeline reads from wherever it is configured. The decision was made during Story 1 implementation and this story reads from that location.
- [x] ~~Should the critic pass be included in the Arm G pipeline?~~ — **Resolved:** No critic in Arm G. The finder-only design was validated in the experiment and is the confirmed choice.
- [x] ~~Should findings be stored in a database to support adding nodes and re-analyzing links freely?~~ — **Resolved:** No database. Findings are stored as per-link files, consistent with the rest of the engine's file-based state. The demo requirement — two workstreams, add a node, analyze links freely — is fully met by keying each result to its link on disk, so re-analysis and new-link analysis are independent. A database adds setup and migration risk with no capability gain for this demo.
