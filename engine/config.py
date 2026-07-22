"""Cluster manifest for the locked technology-risk demo corpus.

Defines which documents make up the demo cluster, their `document_id`s,
provenance (published vs. mock draft), and the curated baseline edges that
seed the knowledge graph before any LLM-found connections are added. This is
the single source of truth the build pipeline reads from — nothing here is
inferred from filenames.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]

# Load a repo-root `.env` if present so a copied+filled template "just works"
# with no manual `export`. This must run before the AZURE_FOUNDRY_* /
# *_DEPLOYMENT reads below. `load_dotenv` no-ops when the file is absent (CI
# has none) and does not override already-exported real env vars.
load_dotenv(REPO_ROOT / ".env")
CORPUS_DIR = REPO_ROOT / "data" / "corpus"

CLUSTER = "technology-risk"
# The Reconciliation Workbench's analysed VEHICLE document lives in its own
# cluster tag so it is never conflated with the legacy technology-risk demo
# cluster (which remains for the inert supervisor/pairwise paths).
AI_CLUSTER = "ai-financial-sector"

# One entry per document *version*. A policy with more than one version
# (e.g. rmit) has one manifest entry per document_id.
DOCUMENTS = {
    "ai-dp-2025": {
        "policy_id": "ai-dp",
        "document_id": "ai-dp-2025",
        "doc_class": "structured-rules",
        "title": (
            "Discussion Paper on Artificial Intelligence in the Malaysian "
            "Financial Sector"
        ),
        "version": "Discussion Paper · Aug 2025",
        "effective_date": None,
        "source_path": CORPUS_DIR / "dp_ai_financial_sector.pdf",
        "source": "published",
        "cluster": AI_CLUSTER,
        # The vehicle document analysed paragraph-by-paragraph by the workbench.
        # Its stylised "AI" logotype is mis-read as "Al"/"$A l$"/"GenAl" by both
        # the default extractor and Azure DI, so its build path — and ONLY its
        # path — runs `engine.ingest.normalise_glyph_artifacts`. The bare Al→AI
        # repair is DP-specific and must not touch other corpus PDFs, so it is
        # gated on this flag rather than wired globally (see engine/build.py).
        "normalise_glyphs": True,
    },
    "rmit-v1-2023": {
        "policy_id": "rmit",
        "document_id": "rmit-v1-2023",
        "doc_class": "structured-rules",
        "title": "Risk Management in Technology (RMiT)",
        "version": "v1 · 2023",
        "effective_date": "2023-06-01",
        "source_path": CORPUS_DIR / "PD-RMiT-June2023.pdf",
        "source": "published",
        "cluster": CLUSTER,
    },
    "rmit-v2-2025": {
        "policy_id": "rmit",
        "document_id": "rmit-v2-2025",
        "doc_class": "structured-rules",
        "title": "Risk Management in Technology (RMiT)",
        "version": "v2 · 2025",
        "effective_date": "2025-11-28",
        "source_path": CORPUS_DIR / "pd-rmit-nov25.pdf",
        "source": "published",
        "cluster": CLUSTER,
    },
    "outsourcing-v1-2019": {
        "policy_id": "outsourcing",
        "document_id": "outsourcing-v1-2019",
        "doc_class": "structured-rules",
        "title": "Outsourcing",
        "version": "v1 · 2019",
        "effective_date": "2019-10-23",
        "source_path": CORPUS_DIR / "PD_Outsourcing_20191023.pdf",
        "source": "published",
        "cluster": CLUSTER,
    },
    "bcm-v1-2022": {
        "policy_id": "bcm",
        "document_id": "bcm-v1-2022",
        "doc_class": "structured-rules",
        "title": "Business Continuity Management",
        "version": "v1 · 2022",
        "effective_date": "2022-12-19",
        "source_path": CORPUS_DIR / "PD-BCM.pdf",
        "source": "published",
        "cluster": CLUSTER,
    },
    "opres-v1-2025-draft": {
        "policy_id": "opres",
        "document_id": "opres-v1-2025-draft",
        "doc_class": "structured-rules",
        "title": "Operational Resilience",
        "version": "draft · Discussion Paper 2025",
        "effective_date": "2025-12-19",
        "source_path": CORPUS_DIR / "dp_operationalresilience_Dec2025.pdf",
        "source": "draft",
        "cluster": CLUSTER,
    },
    "recovery-planning-v1-2021": {
        "policy_id": "recovery-planning",
        "document_id": "recovery-planning-v1-2021",
        "doc_class": "structured-rules",
        "title": "Recovery Planning",
        "version": "v1 · 2021",
        "effective_date": "2021-07-28",
        "source_path": CORPUS_DIR / "pd_Recovery Planning.pdf",
        "source": "published",
        "cluster": CLUSTER,
    },
    "customer-info-v1-2025": {
        "policy_id": "customer-info",
        "document_id": "customer-info-v1-2025",
        "doc_class": "structured-rules",
        "title": "Management of Customer Information",
        "version": "v1 · 2025",
        "effective_date": "2025-10-31",
        "source_path": CORPUS_DIR / "MCIPD_PD_2025.pdf",
        "source": "published",
        "cluster": CLUSTER,
    },
    "open-finance-v1-2025-ed": {
        "policy_id": "open-finance",
        "document_id": "open-finance-v1-2025-ed",
        "doc_class": "structured-rules",
        "title": "Open Finance",
        "version": "ED · 18 Nov 2025",
        "effective_date": "2025-11-18",
        "source_path": CORPUS_DIR / "ED_Open_Finance_2025.pdf",
        "source": "draft",
        "cluster": "open-finance",
    },
}

# Curated seed edges — the deterministic baseline "which policies connect at
# all" for the locked demo cluster, matching the POC's hand-written edges
# (docs/poc/policy-consistency-ai/index.html lines 141-148). Clause anchors
# below are the specific clause numbers each `reason` text names, and every one
# has been validated against the REAL parsed clause index (data/artifacts/
# clause-index.json) — the earlier placeholder anchors (Operational Resilience
# 6.11, BCM 5.1, Customer Info 8.1) did not exist in the corpus and were
# corrected to the real clauses whose text supports each edge's reason. The
# rmit<->outsourcing pair (RMiT 17 vs. Outsourcing 12.1) is the hero conflict
# validated by the discovery brief's blind test. `graph.build_graph`'s
# validation against the supplied `ClauseIndex` enforces "every anchor
# resolves", so any future corpus change that drops one of these clauses fails
# the build loudly rather than shipping a dangling citation.
CURATED_SEED_EDGES = [
    {
        "source_policy_id": "rmit",
        "target_policy_id": "opres",
        "type": "overlaps",
        "reason": (
            "Both govern the continuity of critical services that depend on "
            "cloud/third parties. RMiT 10.50 (cloud risk assessment) overlaps "
            "Operational Resilience 1.1 (continuity of critical financial "
            "services amid deeper third-party dependencies) — a change in one "
            "can duplicate or contradict the other."
        ),
        "source_clauses": ["RMiT 10.50"],
        "target_clauses": ["Operational Resilience 1.1"],
        "provenance": "curated",
        "confidence": 1.0,
    },
    {
        "source_policy_id": "rmit",
        "target_policy_id": "outsourcing",
        "type": "overlaps",
        "reason": (
            "A public-cloud arrangement is often also a material outsourcing. "
            "RMiT clause 17 (cloud consultation/notification) interacts with "
            "Outsourcing 12.1 (written approval) — the core conflict in this "
            "cluster."
        ),
        "source_clauses": ["RMiT 17.1", "RMiT 17.2"],
        "target_clauses": ["Outsourcing 12.1"],
        "provenance": "curated",
        "confidence": 1.0,
    },
    {
        "source_policy_id": "rmit",
        "target_policy_id": "bcm",
        "type": "overlaps",
        "reason": (
            "Cloud services supporting critical operations must have "
            "continuity arrangements. RMiT 17.1 (cloud adoption for critical "
            "systems) engages BCM 9.17 (documenting essential services and the "
            "systems that support them)."
        ),
        "source_clauses": ["RMiT 17.1"],
        "target_clauses": ["BCM 9.17"],
        "provenance": "curated",
        "confidence": 1.0,
    },
    {
        "source_policy_id": "rmit",
        "target_policy_id": "customer-info",
        "type": "overlaps",
        "reason": (
            "Cloud adoption for critical systems often processes customer data "
            "offshore. RMiT 17.1 (cloud adoption) engages Customer Info 13.3 "
            "(control measures over the disclosure of customer information)."
        ),
        "source_clauses": ["RMiT 17.1"],
        "target_clauses": ["Customer Info 13.3"],
        "provenance": "curated",
        "confidence": 1.0,
    },
    {
        "source_policy_id": "opres",
        "target_policy_id": "bcm",
        "type": "overlaps",
        "reason": (
            "Operational resilience and business continuity overlap on the "
            "continuity of critical/essential services after disruption. "
            "Operational Resilience 1.1 (continuity of critical financial "
            "services) overlaps BCM 9.17 (identified essential services and "
            "their supporting systems)."
        ),
        "source_clauses": ["Operational Resilience 1.1"],
        "target_clauses": ["BCM 9.17"],
        "provenance": "curated",
        "confidence": 1.0,
    },
    {
        "source_policy_id": "outsourcing",
        "target_policy_id": "customer-info",
        "type": "overlaps",
        "reason": (
            "Outsourcing (incl. cloud) that involves a service provider "
            "handling customer data engages the Management of Customer "
            "Information rules. Outsourcing 12.1 (approval for material "
            "outsourcing) engages Customer Info 10.35 (engaging an outsourced "
            "service provider that handles customer information)."
        ),
        "source_clauses": ["Outsourcing 12.1"],
        "target_clauses": ["Customer Info 10.35"],
        "provenance": "curated",
        "confidence": 1.0,
    },
]

REFERENCES_DIR = REPO_ROOT / "data" / "references"

# External reference documents (#26 Reference Radar). The external analogue of
# DOCUMENTS: each becomes a `kind:"reference"` graph node rather than a policy
# node. A PUBLIC reference carries a single hand-anchored `passage` — the exact
# verbatim excerpt, extracted from the real public source (the provenance file
# named in `source_path`, and its sibling PDF, live in data/references/) — that
# enters the clause index as ONE clause keyed by `{PolicyShortName} {anchor}`
# (e.g. "PDPA 129"). RESTRICTED (the BNM handbook) and PREVIEW (the trend band)
# references are node-only: no `passage`, no `source_path`, nothing ingested —
# defence in depth for the one confidential item (there is no handbook text in
# any artifact to leak). See data/references/README.md for the source URLs and
# the PDPA §129 amendment-reconstruction note.
REFERENCE_DOCUMENTS = {
    "mas-trm-2021": {
        "policy_id": "mas-trm",
        "document_id": "mas-trm-2021",
        "title": "Technology Risk Management Guidelines (MAS, Singapore)",
        "version": "2021",
        "cluster": CLUSTER,
        "kind": "reference",
        "source_type": "peer_regulator",
        "access": "public",
        "preview": False,
        "source_url": (
            "https://www.mas.gov.sg/regulation/guidelines/"
            "technology-risk-management-guidelines"
        ),
        "source_path": REFERENCES_DIR / "mas-trm-2021.md",
        "anchor": "Cloud",  # → "MAS TRM Cloud"
        "heading": "Section 3.4.2 — Management of Third Party Services (2021)",
        "passage": (
            "The FI should assess and manage its exposure to technology risks "
            "that may affect the confidentiality, integrity and availability of "
            "the IT systems and data at the third party before entering into a "
            "contractual agreement or partnership."
        ),
    },
    "pdpa-2010": {
        "policy_id": "pdpa",
        "document_id": "pdpa-2010",
        "title": "Personal Data Protection Act 2010 (Malaysia)",
        "version": "2010 · Act 709 (as amended by Act A1727)",
        "cluster": CLUSTER,
        "kind": "reference",
        "source_type": "act",
        "access": "public",
        "preview": False,
        "source_url": "https://www.pdp.gov.my/ppdpv1/en/akta/pdp-act-2010-en/",
        "source_path": REFERENCES_DIR / "pdpa-2010.md",
        "mother_document": "Personal Data Protection Act 2010",
        "precedence": "national statute",
        "legislated": True,
        "standard_setting_party": "Parliament of Malaysia",
        "doc_class": "principle",
        "anchor": "129",  # → "PDPA 129"
        "heading": (
            "Section 129(2) — transfer of personal data outside Malaysia "
            "(as amended by Act A1727)"
        ),
        "passage": (
            "A data controller may transfer any personal data of a data subject "
            "to any place outside Malaysia if— (a) there is in that place in "
            "force any law which is substantially similar to this Act; or (b) "
            "that place ensures an adequate level of protection in relation to "
            "the processing of personal data which is at least equivalent to the "
            "level of protection afforded by this Act."
        ),
    },
    "basel-por-2021": {
        "policy_id": "basel-por",
        "document_id": "basel-por-2021",
        "title": "Principles for Operational Resilience (Basel Committee)",
        "version": "2021",
        "cluster": CLUSTER,
        "kind": "reference",
        "source_type": "standard",
        "access": "public",
        "preview": False,
        "source_url": "https://www.bis.org/bcbs/publ/d516.htm",
        "source_path": REFERENCES_DIR / "basel-por-2021.md",
        "anchor": "TP-1",  # → "Basel POR TP-1"
        "heading": "Principle 5 — Third-party dependency management (2021)",
        "passage": (
            "Banks should manage their dependencies on relationships, including "
            "those of, but not limited to, third parties or intragroup entities, "
            "for the delivery of critical operations."
        ),
    },
    # AI source library (source-connection engine) — the curated sources the
    # workbench connects the AI DP's paragraphs to. Verbatim `passage` text is
    # inherited from the reviewed demo snapshot (web/public/data/); each source's
    # per-connection `verification` marker (verified vs illustrative) lives on the
    # verdict record, not here. A source cited at more than one clause carries a
    # `passages` list (one graph node, several verbatim clauses).
    "bcbs-239": {
        "policy_id": "bcbs-239",
        "document_id": "bcbs-239",
        "title": "BCBS 239 — Principles for effective risk data aggregation",
        "version": "2013 · BCBS d239",
        "cluster": AI_CLUSTER,
        "kind": "reference",
        "source_type": "international_standard",
        "access": "public",
        "preview": False,
        "source_url": "https://www.bis.org/publ/bcbs239.htm",
        "mother_document": "Basel Committee on Banking Supervision",
        "precedence": "international standard",
        "legislated": False,
        "standard_setting_party": "Basel Committee on Banking Supervision",
        "doc_class": "principle",
        "passages": [
            {
                "anchor": "P4",  # → "BCBS 239 P4"
                "heading": "Principle 4 — Completeness",
                "passage": (
                    "A bank should be able to capture and aggregate all material "
                    "risk data across the banking group. Data should be available "
                    "by business line, legal entity, asset type, industry, region "
                    "and other groupings."
                ),
            },
            {
                "anchor": "P3",  # → "BCBS 239 P3"
                "heading": "Principle 3 — Accuracy and Integrity",
                "passage": (
                    "A bank should be able to generate accurate and reliable risk "
                    "data to meet normal and stress/crisis reporting accuracy "
                    "requirements. Data should be aggregated on a largely "
                    "automated basis so as to minimise the probability of errors."
                ),
            },
        ],
    },
    "oecd-ai": {
        "policy_id": "oecd-ai",
        "document_id": "oecd-ai",
        "title": "OECD AI Principles",
        "version": "2019 (rev. 2024)",
        "cluster": AI_CLUSTER,
        "kind": "reference",
        "source_type": "international_standard",
        "access": "public",
        "preview": False,
        "source_url": "https://oecd.ai/en/ai-principles",
        "mother_document": "OECD Recommendation on Artificial Intelligence",
        "precedence": "international standard",
        "legislated": False,
        "standard_setting_party": "OECD",
        "doc_class": "principle",
        "anchor": "1.2",  # → "OECD 1.2"
        "heading": "Principle 1.2 — Human agency and oversight",
        "passage": (
            "AI actors should implement mechanisms and safeguards, such as "
            "capacity for human agency and oversight, including to address risks "
            "arising from uses outside of intended purpose."
        ),
    },
    "nist-ai-rmf": {
        "policy_id": "nist-ai-rmf",
        "document_id": "nist-ai-rmf",
        "title": "NIST AI Risk Management Framework",
        "version": "AI RMF 1.0 · 2023",
        "cluster": AI_CLUSTER,
        "kind": "reference",
        "source_type": "international_standard",
        "access": "public",
        "preview": False,
        "source_url": "https://www.nist.gov/itl/ai-risk-management-framework",
        "mother_document": "NIST AI Risk Management Framework (AI RMF 1.0)",
        "precedence": "international standard",
        "legislated": False,
        "standard_setting_party": "NIST (US Department of Commerce)",
        "doc_class": "technical",
        "anchor": "MEASURE 2.11",  # → "NIST MEASURE 2.11"
        "heading": "MEASURE 2.11 — Fairness and bias evaluation",
        "passage": (
            "Fairness and bias — as identified in the MAP function — are "
            "evaluated and results are documented, including the demographic "
            "groups and contexts assessed."
        ),
    },
    "bnm-ftfc": {
        "policy_id": "bnm-ftfc",
        "document_id": "bnm-ftfc",
        "title": "BNM Fair Treatment of Financial Consumers",
        "version": "2019",
        "cluster": AI_CLUSTER,
        "kind": "reference",
        "source_type": "internal_bnm",
        "access": "public",
        "preview": False,
        "source_url": "https://www.bnm.gov.my/-/fair-treatment-of-financial-consumers",
        "mother_document": "Fair Treatment of Financial Consumers",
        "precedence": "domestic regulation",
        "legislated": True,
        "standard_setting_party": "Bank Negara Malaysia",
        "doc_class": "principle",
        "anchor": "8.1",  # → "FTFC 8.1"
        "heading": "8.1 — Fair treatment at all stages",
        "passage": (
            "A financial service provider must ensure that financial consumers "
            "are treated fairly at all stages of their relationship with the "
            "financial service provider."
        ),
    },
    "eu-ai-act": {
        "policy_id": "eu-ai-act",
        "document_id": "eu-ai-act",
        "title": "EU AI Act (Regulation 2024/1689)",
        "version": "Regulation (EU) 2024/1689",
        "cluster": AI_CLUSTER,
        "kind": "reference",
        "source_type": "act",
        "access": "public",
        "preview": False,
        "source_url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
        "mother_document": "Regulation (EU) 2024/1689 (Artificial Intelligence Act)",
        "precedence": "foreign statute",
        "legislated": True,
        "standard_setting_party": "European Parliament and Council",
        "doc_class": "principle",
        "anchor": "Art 50",  # → "EU AI Act Art 50"
        "heading": "Article 50 — Transparency obligations for generative AI",
        "passage": (
            "Providers of AI systems generating synthetic audio, image, video or "
            "text content shall ensure that the outputs of the AI system are "
            "marked in a machine-readable format and detectable as artificially "
            "generated or manipulated."
        ),
    },
    # Industry-feedback sources (Task 3) — consultation responses to the DP. Each
    # carries a `stance` (agree | partial | disagree). Their passages are
    # illustrative (representative of the sector's position, not a byte-verbatim
    # quote of one respondent); that is recorded by the verdict record's
    # `verification: "illustrative"` marker, never presented as verified.
    "industry-fsp-3": {
        "policy_id": "industry-fsp-3",
        "document_id": "industry-fsp-3",
        "title": "Industry feedback — 3 FSP respondents",
        "version": "consultation response",
        "cluster": AI_CLUSTER,
        "kind": "reference",
        "source_type": "industry_feedback",
        "access": "public",
        "preview": False,
        "stance": "partial",
        "precedence": "industry feedback",
        "legislated": False,
        "standard_setting_party": "3 FSP respondents",
        "anchor": "FSP-3",  # → "Industry FSP-3"
        "heading": "FSP respondents — data & personal information",
        "passage": (
            "The requirement to obtain informed consent is unworkable for models "
            "already trained on legacy datasets collected before AI use was "
            "contemplated."
        ),
    },
    "industry-aob": {
        "policy_id": "industry-aob",
        "document_id": "industry-aob",
        "title": "Association of Banks industry feedback",
        "version": "consultation response",
        "cluster": AI_CLUSTER,
        "kind": "reference",
        "source_type": "industry_feedback",
        "access": "public",
        "preview": False,
        "stance": "agree",
        "precedence": "industry feedback",
        "legislated": False,
        "standard_setting_party": "Association of Banks",
        "anchor": "AoB",  # → "Industry AoB"
        "heading": "Association of Banks — generative AI oversight",
        "passage": (
            "Members support a risk-proportionate approach to human review of "
            "generative AI outputs, focused on customer-facing and "
            "decision-critical use cases."
        ),
    },
    # Node-only references (no passage, never ingested) ----------------------
    "bnm-handbook": {
        "policy_id": "bnm-handbook",
        "document_id": "bnm-handbook",
        "title": "Regulatory Handbook (BNM)",
        "version": "internal",
        "cluster": CLUSTER,
        "kind": "reference",
        "source_type": "handbook",
        "access": "restricted",  # confidential → passages never ingested
        "preview": False,
    },
    "trend-cloud-signals": {
        "policy_id": "trend-cloud-signals",
        "document_id": "trend-cloud-signals",
        "title": "Trends · News · foreign policies",
        "version": "preview",
        "cluster": CLUSTER,
        "kind": "reference",
        "source_type": "trend",
        "access": "public",
        "preview": True,  # labelled preview → no verbatim excerpt
    },
    # A public peer-regulator source the finder identifies but cannot fetch (the
    # MAS site blocks automated access). Node-only: no passage is ingested, so it
    # carries no quote. Its connection is surfaced as `could_not_retrieve` on the
    # verdict record (Task 4) — never a fabricated verdict or quote.
    "mas-feat": {
        "policy_id": "mas-feat",
        "document_id": "mas-feat",
        "title": "MAS — FEAT Principles (Fairness)",
        "version": "2018",
        "cluster": AI_CLUSTER,
        "kind": "reference",
        "source_type": "peer_regulator",
        "access": "public",
        "preview": False,
        "source_url": "https://www.mas.gov.sg/publications/monographs-or-information-paper/2018/feat",
        "mother_document": "MAS FEAT Principles",
        "precedence": "peer regulator guidance",
        "legislated": False,
        "standard_setting_party": "Monetary Authority of Singapore",
        "doc_class": "principle",
    },
}

# Reference↔clause edges (`type:"references"`, #26). All originate from the
# current `rmit` document (resolved per-policy by `_current_document_id`). Public
# reference edges are `provenance:"llm-found"` with a frozen per-edge confidence
# (the output of a one-off finder pass, frozen-as-fixture) — this both satisfies
# the engine invariant (a `curated` edge MUST be confidence 1.0, so a sub-1.0
# demo confidence cannot be curated) and gives #8 the real per-edge score it
# renders. The restricted-handbook and preview-trend edges carry no model score
# and are `curated`, confidence 1.0 placeholders; their `target_clauses` is a
# provenance LABEL, not an ingested clause — `build_graph`'s validator exempts a
# restricted/preview target from the "every target clause resolves" check.
REFERENCE_SEED_EDGES = [
    {
        "source_policy_id": "rmit",
        "target_policy_id": "mas-trm",
        "type": "references",
        "reason": (
            "MAS governs cloud through third-party risk management — assess "
            "technology risk before contracting, manage it on an ongoing basis "
            "— not pre-approval. The peer benchmark for 17.1's shift from "
            "consultation to 14-day notification."
        ),
        "source_clauses": ["RMiT 17.1"],
        "target_clauses": ["MAS TRM Cloud"],
        "provenance": "llm-found",
        "confidence": 0.88,
    },
    {
        "source_policy_id": "rmit",
        "target_policy_id": "pdpa",
        "type": "references",
        "reason": (
            "A cloud region outside Malaysia engages the PDPA's cross-border "
            "transfer test (substantially similar law or adequate protection), "
            "so the 17.1 notification should still capture data residency once "
            "the requirement to consult the Bank is removed."
        ),
        "source_clauses": ["RMiT 17.1"],
        "target_clauses": ["PDPA 129"],
        "provenance": "llm-found",
        "confidence": 0.90,
    },
    {
        "source_policy_id": "rmit",
        "target_policy_id": "basel-por",
        "type": "references",
        "reason": (
            "The international baseline keeps responsibility for third-party "
            "(incl. cloud) dependencies with the bank whatever the approval "
            "model — 17.1 must preserve that."
        ),
        "source_clauses": ["RMiT 17.1"],
        "target_clauses": ["Basel POR TP-1"],
        "provenance": "llm-found",
        "confidence": 0.84,
    },
    {
        "source_policy_id": "rmit",
        "target_policy_id": "bnm-handbook",
        "type": "references",
        "reason": (
            "Listed so the drafter knows the handbook connects to this clause; "
            "its content is confidential and deferred from MVP1."
        ),
        "source_clauses": ["RMiT 17.1"],
        "target_clauses": ["BNM Handbook — Cloud & Outsourcing Manual"],
        "provenance": "curated",
        "confidence": 1.0,
    },
    {
        "source_policy_id": "rmit",
        "target_policy_id": "trend-cloud-signals",
        "type": "references",
        "reason": (
            "Signals such as in-country cloud regions and EU DORA — a "
            "what's-next preview, not a committed reference."
        ),
        "source_clauses": ["RMiT 17.1"],
        "target_clauses": ["Trend — in-country cloud regions"],
        "provenance": "curated",
        "confidence": 1.0,
    },
]

# Frozen connection fixtures for the vehicle DP's three showcase paragraphs
# (3.5 / 3.11 / 4.6). These are the output of a one-off two-branch finder pass,
# FROZEN-as-fixture so the offline build is deterministic and credential-free —
# the same pattern as `REFERENCE_SEED_EDGES`' frozen `confidence`. Each carries a
# `branch` (cited | uncited | feedback), a `source_document_id` + `clause_number`
# joining to the graph node + verbatim clause, a hand-set `verdict` + `rationale`,
# a `confidence_score` the deterministic band formula (engine.verdicts) maps to
# High/Medium/Low, and a `verification` marker (verified vs illustrative). In
# production the SAME verdict stage consumes real per-connection finder scores via
# the injectable `verdict_fn`; the fixtures are the demo stand-in, not a claim of
# live confidence. A blocked source carries `status: "could_not_retrieve"` and no
# clause — surfaced honestly, never a fabricated verdict.
AI_DP_CONNECTIONS = [
    # --- Paragraph 3.5 · Fair usage & bias ---------------------------------
    {
        "id": "ai-dp-2025:3.5::oecd:OECD 1.2",
        "paragraph": "3.5",
        "branch": "cited",
        "source_document_id": "oecd-ai",
        "clause_number": "OECD 1.2",
        "verdict": "Consensus",
        "confidence_score": 0.87,
        "verification": "verified",
        "rationale": (
            "OECD backs the fairness stance and adds a human-agency & oversight "
            "mechanism paragraph 3.5 does not yet name."
        ),
    },
    {
        "id": "ai-dp-2025:3.5::nist:NIST MEASURE 2.11",
        "paragraph": "3.5",
        "branch": "uncited",
        "source_document_id": "nist-ai-rmf",
        "clause_number": "NIST MEASURE 2.11",
        "verdict": "Gap",
        "confidence_score": 0.80,
        "verification": "verified",
        "rationale": (
            "NIST calls for a pre-deployment bias assessment across demographic "
            "groups that paragraph 3.5 does not require."
        ),
    },
    {
        "id": "ai-dp-2025:3.5::ftfc:FTFC 8.1",
        "paragraph": "3.5",
        "branch": "uncited",
        "source_document_id": "bnm-ftfc",
        "clause_number": "FTFC 8.1",
        "verdict": "Duplicate",
        "confidence_score": 0.78,
        "verification": "illustrative",
        "rationale": (
            "The fair-treatment obligation already covers non-discriminatory "
            "outcomes; 3.5 restates it for AI rather than cross-referencing."
        ),
    },
    {
        "id": "ai-dp-2025:3.5::mas-feat",
        "paragraph": "3.5",
        "branch": "uncited",
        "source_document_id": "mas-feat",
        "status": "could_not_retrieve",
        "reason": (
            "Identified as a likely peer benchmark for 3.5, but the MAS site "
            "blocks automated access. Upload the source to analyse this "
            "connection."
        ),
    },
    # --- Paragraph 3.11 · GenAI hallucinations -----------------------------
    {
        "id": "ai-dp-2025:3.11::bcbs239:BCBS 239 P3",
        "paragraph": "3.11",
        "branch": "cited",
        "source_document_id": "bcbs-239",
        "clause_number": "BCBS 239 P3",
        "verdict": "Consensus",
        "confidence_score": 0.88,
        "verification": "verified",
        "rationale": (
            "BCBS 239's accuracy-and-integrity principle supports 3.11's call "
            "for controls over erroneous outputs."
        ),
    },
    {
        "id": "ai-dp-2025:3.11::euaiact:EU AI Act Art 50",
        "paragraph": "3.11",
        "branch": "uncited",
        "source_document_id": "eu-ai-act",
        "clause_number": "EU AI Act Art 50",
        "verdict": "Gap",
        "confidence_score": 0.80,
        "verification": "verified",
        "rationale": (
            "The EU AI Act requires generative outputs to be marked as "
            "AI-generated — a transparency obligation 3.11 does not impose."
        ),
    },
    {
        "id": "ai-dp-2025:3.11::industry-aob",
        "paragraph": "3.11",
        "branch": "feedback",
        "source_document_id": "industry-aob",
        "clause_number": "Industry AoB",
        "verdict": "Consensus",
        "confidence_score": 0.79,
        "verification": "illustrative",
        "stance": "agree",
        "rationale": (
            "The Association of Banks agrees that human review of generative "
            "outputs should be proportionate to their impact — reinforcing 3.11."
        ),
    },
    # --- Paragraph 4.6 · Data & personal information -----------------------
    {
        "id": "ai-dp-2025:4.6::pdpa-2010:PDPA 129",
        "paragraph": "4.6",
        "branch": "uncited",
        "source_document_id": "pdpa-2010",
        "clause_number": "PDPA 129",
        "verdict": "Conflict",
        "confidence_score": 0.90,
        "verification": "verified",
        "rationale": (
            "4.6 relies on broad informed consent; PDPA §129 sets a specific "
            "cross-border transfer test the draft does not cite and appears to "
            "conflict with."
        ),
    },
    {
        "id": "ai-dp-2025:4.6::bcbs239:BCBS 239 P4",
        "paragraph": "4.6",
        "branch": "cited",
        "source_document_id": "bcbs-239",
        "clause_number": "BCBS 239 P4",
        "verdict": "Consensus",
        "confidence_score": 0.88,
        "verification": "verified",
        "rationale": (
            "BCBS 239's completeness principle supports 4.6's expectation of "
            "governed, complete data handling."
        ),
    },
    {
        "id": "ai-dp-2025:4.6::industry-fsp-3",
        "paragraph": "4.6",
        "branch": "feedback",
        "source_document_id": "industry-fsp-3",
        "clause_number": "Industry FSP-3",
        "verdict": "Partial",
        "confidence_score": 0.78,
        "verification": "illustrative",
        "stance": "partial",
        "rationale": (
            "The sector supports responsible data handling but rejects the "
            "informed-consent mechanism for legacy datasets — agrees in part, "
            "diverges in part."
        ),
    },
]

# Azure AI Foundry access — read from env, never hardcoded/committed.
AZURE_FOUNDRY_ENDPOINT = os.environ.get("AZURE_FOUNDRY_ENDPOINT")
AZURE_FOUNDRY_API_KEY = os.environ.get("AZURE_FOUNDRY_API_KEY")

# Deployment names are configurable via env, with the confirmed defaults
# from the spec (resource aih-semantic-kernel-swc, swedencentral).
PARSER_DEPLOYMENT = os.environ.get("AZURE_FOUNDRY_PARSER_DEPLOYMENT", "claude-sonnet-5")
FINDER_CRITIC_DEPLOYMENT = os.environ.get(
    "AZURE_FOUNDRY_FINDER_CRITIC_DEPLOYMENT", "claude-opus-4-8"
)

# Azure AI Document Intelligence — optional PDF ingestion backend. When both the
# endpoint and key are set, `engine.ingest` routes PDFs through the
# `prebuilt-layout` model, which reconstructs reading order (columns, list
# labels, headings) that the default MarkItDown extractor scrambles on BNM's
# multi-column PDFs. Unset → the default extractor is used (no behaviour change,
# no Azure dependency in CI). Read from env, never committed.
DOCINTEL_ENDPOINT = os.environ.get("AZURE_DOCINTEL_ENDPOINT")
DOCINTEL_API_KEY = os.environ.get("AZURE_DOCINTEL_API_KEY")
# MarkItDown's DI converter hardcodes an old preview api-version
# (2024-07-31-preview) that GA Document Intelligence resources reject with a
# 404. Override with the GA version the installed SDK (1.x) speaks. Configurable
# in case a resource pins a different version.
DOCINTEL_API_VERSION = os.environ.get("AZURE_DOCINTEL_API_VERSION", "2024-11-30")
