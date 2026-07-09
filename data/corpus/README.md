# Corpus — BNM policy documents (public)

Source documents for the Rulebook Radar knowledge-graph engine (#6). All are
**public** BNM documents from [bnm.gov.my](https://www.bnm.gov.my) — no
confidentiality constraint (internal/sensitive material lives in the git-ignored
`docs/references/`, never here). The build's stage-1 (MarkItDown) ingests these
into clean markdown; nothing here is edited by hand.

This is the **locked 6-document technology-risk cluster** (see
`docs/specs/rulebook-radar/spec-knowledge-graph-engine.md`). There is no standalone
"Cyber Risk" policy — cyber lives inside RMiT.

| File                                   | Document                                                   | Issued      | Role in the demo                                                                                                                                        |
| -------------------------------------- | ---------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pd-rmit-nov25.pdf`                    | Risk Management in Technology (RMiT)                       | 28 Nov 2025 | Real published base → derives **real v1** (superseded) **and** the base the LLM expands into the **mock v2 draft** (17.1 hand-pinned to "notify-after") |
| `PD_Outsourcing_20191023.pdf`          | Outsourcing                                                | 23 Oct 2019 | The hero conflict — clause 12.1 ("written approval before") vs. draft RMiT 17.1                                                                         |
| `PD-BCM.pdf`                           | Business Continuity Management                             | 19 Dec 2022 | In-force cluster node                                                                                                                                   |
| `dp_operationalresilience_Dec2025.pdf` | Operational Resilience (Discussion Paper)                  | 19 Dec 2025 | Grounds the Operational Resilience draft node + its provenance trail                                                                                    |
| `pd_Recovery Planning.pdf`             | Recovery Planning                                          | 28 Jul 2021 | In-force cluster node                                                                                                                                   |
| `MCIPD_PD_2025.pdf`                    | Management of Customer Information & Permitted Disclosures | 31 Oct 2025 | In-force cluster node (data-privacy edge; replaced the dropped Cyber node)                                                                              |

Plus a greyed **AML/CFT** cross-cluster preview node (not a document here — it is a
labelled "what's next" placeholder in the graph).

**Note:** the authoritative filename → `document_id` mapping is defined in
`engine/config.py` (the build does not infer it from filenames). This table is the
human-readable reference.

## Testing another cluster (bring your own documents)

The engine is not hard-wired to these six files — they are the _default demo
cluster_, but the pipeline works on any set of clause-numbered policy PDFs. To
try a different cluster (e.g. a payments or AML/CFT cluster):

1. **Drop the PDFs here** in `data/corpus/` (public documents only — never place
   anything sensitive here; that belongs in the git-ignored `docs/references/`).
2. **Point `engine/config.py` at them.** Edit `DOCUMENTS` so each entry's
   `source_path` names your file and set its `policy_id`, `document_id`,
   `title`, `version`, and `source`. Add each new `policy_id` to
   `POLICY_SHORT_NAMES` in `engine/clauses.py` (the canonical clause-number
   prefix, e.g. `"payments": "Payments"`).
3. **Update `CURATED_SEED_EDGES`** (also in `config.py`) to the connections you
   want as the baseline graph — every clause an edge cites must resolve in the
   parsed index, or `build_graph` fails loudly (by design).
4. **Run `python -m engine.build`.** Clause parsing is deterministic and
   network-free; only PDF ingestion needs the Azure Document Intelligence
   credentials in `.env` (see `.env.example`). Inspect
   `data/artifacts/_ingest/<document_id>.md` (git-ignored debug dump) if a
   document parses poorly, and `data/artifacts/dropped-clauses.json` for any
   clause the segmenter could not place.

The clause grammar the segmenter recognises (numbered clauses inline or
label-alone, `(a)`/`(i)` sub-items, `Appendix N`, section headings) matches BNM
conventions; a corpus with very different numbering may need the regexes in
`engine/clauses.py` extended. Nothing else about the cluster is hard-coded.
