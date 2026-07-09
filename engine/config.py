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
MOCK_DIR = REPO_ROOT / "data" / "mock"

CLUSTER = "technology-risk"

# One entry per document *version*. A policy with more than one version
# (e.g. rmit) has one manifest entry per document_id.
DOCUMENTS = {
    "rmit-v1-2020": {
        "policy_id": "rmit",
        "document_id": "rmit-v1-2020",
        "title": "Risk Management in Technology (RMiT)",
        "version": "v1 · 2020",
        "effective_date": "2025-11-28",
        "source_path": CORPUS_DIR / "pd-rmit-nov25.pdf",
        "source": "published",
        "cluster": CLUSTER,
    },
    "rmit-v2-2026-draft": {
        "policy_id": "rmit",
        "document_id": "rmit-v2-2026-draft",
        "title": "Risk Management in Technology (RMiT)",
        "version": "v2 · 2026 draft",
        "effective_date": None,
        "source_path": MOCK_DIR / "rmit-v2-2026-draft.md",
        "source": "draft",
        "cluster": CLUSTER,
        "provenance": (
            "generation: llm-expanded from rmit-v1-2020; 17.x hand-authored; "
            "reviewed 2026-07-08"
        ),
    },
    "outsourcing-v1-2019": {
        "policy_id": "outsourcing",
        "document_id": "outsourcing-v1-2019",
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
        "title": "Management of Customer Information",
        "version": "v1 · 2025",
        "effective_date": "2025-10-31",
        "source_path": CORPUS_DIR / "MCIPD_PD_2025.pdf",
        "source": "published",
        "cluster": CLUSTER,
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
}

# Reference↔clause edges (`type:"references"`, #26). All originate from the
# single editable draft (rmit-v2-2026-draft, the current `rmit` version). Public
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
