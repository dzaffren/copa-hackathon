# Policy ingestion & rulebook knowledge-graph engine

**Ticket:** TBD
**Type:** Technical — Data pipeline / Infrastructure

This is the foundational data layer for Rulebook Radar. It turns a cluster of
Bank Negara Malaysia's published policy documents into clean, structured text
with every clause individually addressable and quotable, and assembles those
documents into a knowledge graph whose links describe how the policies connect,
overlap, depend on, and supersede one another. It has no screen of its own —
every other story (drafter workspace, ripple check, drafting copilot, supervisor
completeness check, reviewer workflow) reads from this engine. It also ingests
sensitive bank submissions for the supervisor story using the same clean-text
pipeline.

## Motivation

**Current state:** There is no machine-readable map of how BNM's policies
connect — the relationships live in the heads of experienced staff. Worse, the
published policy documents themselves cannot simply be read by software: a
dry-run on the real RMiT and Outsourcing documents showed that naive
text extraction produces gibberish because the documents use custom font
encoding. Without clean text and a way to name and quote each clause exactly,
none of the product's guardrails or features are possible.

**Desired state:** Every document in the demo cluster is converted to clean,
readable text with its clause numbering intact; every clause is retrievable and
quotable word-for-word by its clause number (for example, "Outsourcing 12.1" or
"RMiT 17.1"); and the cluster is represented as a graph where each link carries a
plain-language explanation of why the two policies are connected. The graph can
surface the real cross-policy connections in the corpus without inventing false
ones, and every connection it asserts points to an exact clause that a human can
verify in seconds.

**Trigger:** This is the first thing built and everything depends on it (per the
epic rollout order). The riskiest project assumption — that connections can be
found reliably without hallucination — was validated in a blind test on the real
RMiT and Outsourcing documents, which independently found the clause 17 versus
12.1 conflict and cited every clause word-for-word. That result was made
verifiable only because each claim quoted an existing clause. This engine
operationalises that finding as the permanent foundation.

## Scope

- **In scope:**
  - Converting each published policy document in the demo cluster (RMiT,
    Operational Resilience, Outsourcing, Business Continuity, Cyber Risk) into
    clean, structured text with clause numbers preserved, including documents
    that naive extraction would garble.
  - A clause index: every clause is individually addressable and quotable
    word-for-word by its clause number, faithful to the source document.
  - A knowledge graph: policy documents are the points on the map; the links
    between them describe overlap, reference, and depends-on relationships, and
    each link carries a plain-language explanation of why the two policies are
    connected.
  - Version-lineage links: representing that an older version is superseded by a
    newer version of the same policy.
  - Derived node status: "In progress" when a live working draft exists for a
    policy, otherwise "In force" or "Superseded" as read from the published
    corpus.
  - The connection-finding capability: given the corpus, surfacing the real
    cross-policy connections and conflicts, each anchored to the exact clauses
    it rests on.
  - The anti-hallucination guardrail at the data layer: a candidate connection
    or claim that cannot be anchored to an existing clause is reported as
    unsupported, never invented.
  - Ingesting an uploaded bank submission (in common document formats) into the
    same clean-text form for the supervisor story, held under heavier governance
    than public policy documents.

- **Out of scope:**
  - Any end-user screen or visualisation (owned by the drafter workspace and
    supervisor stories).
  - The ripple/impact analysis that runs when a draft changes (owned by the
    ripple check story) — this engine provides the graph it runs on, not the
    change analysis itself.
  - Writing changes back into a live working draft (owned by the drafting
    copilot story).
  - The supervisor's checklist assembly and Met/Missing/Unclear decision (owned
    by the supervisor story) — this engine provides the clean submission text
    and the graph, not the assessment.
  - Cross-cluster analysis beyond a single labelled preview link — full
    cross-cluster mapping is a future phase.

## Goals

- Convert every document in the demo cluster to clean text with clause numbers
  intact, including documents that naive extraction garbles, with zero
  unreadable output.
- Make 100% of clauses retrievable by clause number, with the returned text
  identical to the source document (the basis for the word-for-word citation
  guardrail).
- Build a graph in which every link carries a human-readable reason and points
  to the specific clauses that justify it.
- On the validated document pair, surface the known real connections (including
  the clause 17 versus Outsourcing 12.1 conflict) while introducing no invented
  connections.
- Derive every node's status correctly from whether a live draft exists and from
  the published corpus, with no manually invented statuses.

## Non-Goals

- Covering the whole BNM rulebook — the engine is scoped to one cluster of 5–10
  related policies.
- Guaranteeing perfect recall across the entire rulebook — the engine targets
  the demo cluster; broad-corpus tuning is a later phase.
- Real-world production data governance for bank submissions — the demo uses
  sample submission data; production access control and retention design is
  deferred and named explicitly in the pitch.

## Success Criteria

- Every document in the locked demo cluster is ingested to clean text; a manual
  spot-check of clause numbers against the original document finds no missing or
  garbled clauses.
- For any clause number in the cluster, the engine returns text that matches the
  source word-for-word, or explicitly reports that no such clause exists.
- Every link in the graph has both a plain-language reason and at least one
  clause reference on each side; no link exists without a reason.
- On the validated RMiT/Outsourcing pair, the engine surfaces the real
  connections found in the blind test and produces no connection that cannot be
  traced to real clauses.
- Every node reports a status that matches the rule "In progress if a live draft
  exists, else In force or Superseded from the corpus."

## Acceptance Criteria

### Scenario: A published policy document is ingested into clean, structured text

```gherkin
Given the published Outsourcing policy document from the demo cluster
When the document is ingested
Then its full text is available in clean, readable form
  And the clause numbering from the original document is preserved
  And clause "Outsourcing 12.1" reads "A financial institution must obtain the Bank's written approval before entering into a new material outsourcing arrangement."
```

### Scenario: A document that naive extraction would garble is ingested cleanly

```gherkin
Given the published RMiT policy document, which uses a custom font encoding that produces unreadable output under naive text extraction
When the document is ingested
Then the resulting text is clean and readable rather than garbled
  And clause "RMiT 17.1" and clause "RMiT 17.2" are each present and readable
  And no clause is reduced to unreadable symbols
```

### Scenario: Every clause is individually addressable and quoted word-for-word

```gherkin
Given the demo cluster has been ingested
When a clause is requested by its clause number
Then the exact text of that clause is returned, identical to the source document
  And the clause number that was requested is returned alongside the text

Examples:
  | clause number   | expected text quoted word-for-word from the source                                                                                          |
  | Outsourcing 12.1 | A financial institution must obtain the Bank's written approval before entering into a new material outsourcing arrangement.                |
  | RMiT 17.1        | The clause governing first-time public-cloud adoption for critical systems, quoted exactly as published                                     |
  | RMiT 17.2        | The clause governing subsequent public-cloud adoption, quoted exactly as published                                                          |
```

### Scenario: Requesting a clause that does not exist is reported honestly

```gherkin
Given the demo cluster has been ingested
When a clause is requested by a clause number that does not exist in the corpus, such as "Outsourcing 99.9"
Then the engine reports that no matching clause was found
  And no substitute or invented clause text is returned
```

### Scenario: The knowledge graph is built with an explanation on every link

```gherkin
Given the demo cluster has been ingested
When the knowledge graph is assembled
Then each policy in the cluster appears as a point on the graph
  And each link between two policies carries a plain-language reason for the connection
  And the link between RMiT and Outsourcing explains that a public-cloud arrangement is often also a material outsourcing, connecting RMiT clause 17 with Outsourcing 12.1
  And the link between RMiT and Operational Resilience explains that both govern the register of critical cloud and third-party services
```

### Scenario: The connection-finding capability surfaces the real cross-policy conflict

```gherkin
Given the RMiT and Outsourcing documents have been ingested
  And RMiT clause 17.1 has been amended so that first-time public-cloud adoption requires notifying the Bank after the fact rather than obtaining approval before
When the engine searches for cross-policy connections between the two documents
Then it surfaces a conflict between RMiT clause 17.1 and Outsourcing clause 12.1
  And the conflict quotes Outsourcing 12.1 word-for-word as requiring written approval before a material outsourcing arrangement
  And the conflict is scoped to cases where the cloud service is also a material outsourcing
  And it surfaces the dependency that RMiT 17.2 relies on a prior 17.1 consultation that the amendment removes
```

### Scenario: A claim with no supporting clause is reported as unsupported, not invented

```gherkin
Given the demo cluster has been ingested
When a candidate connection is considered that cannot be traced to any existing clause in the corpus
Then the engine reports the candidate connection as unsupported
  And it states that no matching clause was found
  And it does not fabricate a clause number or clause text to support the claim
```

### Scenario: Node status is derived from whether a live draft exists

```gherkin
Given the published corpus marks RMiT as the current version and its earlier version as superseded
  And a live working draft exists for RMiT
  And a live working draft exists for Operational Resilience
When the graph reports each node's status
Then RMiT is reported as "In progress" because a live draft exists for it
  And Operational Resilience is reported as "In progress" because a live draft exists for it
  And Business Continuity is reported as "In force" because no live draft exists for it
  And the earlier RMiT version is reported as "Superseded" from the published corpus
  And no node's status is set manually against these rules
```

### Scenario: Version lineage is represented in the graph

```gherkin
Given both the current and the earlier version of RMiT have been ingested
When the graph is assembled
Then a version-lineage link records that the earlier RMiT version is superseded by the current version
  And the current version is reachable from the earlier version through that link
```

### Scenario: A sensitive bank submission is ingested under heavier governance

```gherkin
Given a supervision officer uploads Meridian Bank's cloud outsourcing application as a document
When the submission is ingested
Then its full text is available in clean, readable form using the same conversion as the policy corpus
  And the submission is held as sensitive supervised-entity data, separate from the public policy corpus
  And access to the submission is restricted more tightly than access to the public policy documents
```

### Scenario: An unreadable or unsupported upload is rejected clearly

```gherkin
Given a supervision officer uploads a file that cannot be converted into readable text
When the submission is ingested
Then the engine reports that the document could not be read
  And no partial or garbled text is stored as if it were the submission
  And the officer is told the upload could not be processed
```

## Constraints

- **Backwards compatibility:** New foundational layer; no existing consumers to
  preserve. Later stories will depend on the shape of the clause index and
  graph, so those must be stable once the first consuming story is built.
- **Downtime:** Not applicable for the hackathon demo — the engine builds the
  graph and clause index ahead of the demo from a fixed corpus; there is no live
  service to keep available.
- **Compliance:** Public policy documents carry no confidentiality constraint.
  Uploaded bank submissions are sensitive supervised-entity data and must be
  kept separate from the public corpus and access-restricted; the demo uses
  sample submission data, and real-world data governance is a named
  post-hackathon concern. The word-for-word citation guardrail is a hard rule at
  this layer: no asserted connection or claim without an existing quoted clause.
- **Rollback:** The engine's output (clean text, clause index, graph) is
  derived from the source documents and can be rebuilt from scratch at any time,
  so any faulty build is fully reversible by re-ingesting the corpus.

## Dependencies

- **Locked demo cluster:** the final set of 5–10 technology-risk policies (RMiT,
  Operational Resilience, Outsourcing, Business Continuity, Cyber Risk) must be
  confirmed before build.
- **Published policy documents:** the current published BNM policy documents for
  the cluster (all public).
- **Sample bank submission:** at least one representative cloud outsourcing
  application (sample data) for the supervisor ingestion path, plus a clean
  version so the approve path can be demonstrated downstream.
- **Signal of a live draft:** an agreed way to know that a live working draft
  exists for a policy, so node status can be derived (the draft itself is owned
  by the drafter and copilot stories; this engine only needs to know it exists).

## Open Questions

- [x] ~~Does naive text extraction work on BNM policy documents?~~ —
      **Resolved:** No. A dry-run on the real RMiT and Outsourcing documents
      produced gibberish under naive extraction; a clean-markdown conversion
      preserved clause numbers on both, and is the chosen ingestion approach.
- [x] ~~Should the engine flag only conflicts, or also duplications and gaps?~~ —
      **Resolved:** the engine surfaces the raw connections and their supporting
      clauses; classifying a connection as Conflict, Duplication, or Gap is the
      job of the ripple check story that consumes this engine. The engine must
      provide enough clause-anchored connection detail to make all three
      possible.
- [ ] **What is the exact final cluster (which 5–10 policies)?** —
      **Status:** awaiting confirmation from contacts. Blocks final content, not
      the engine's design.
- [ ] **What governance applies to uploaded bank submissions in a real
      deployment?** — **Deferred (non-blocking):** the demo uses sample data;
      the engine keeps submissions separate and access-restricted, and
      production-grade governance is a named post-hackathon concern.
