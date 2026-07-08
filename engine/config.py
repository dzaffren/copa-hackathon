"""Cluster manifest for the locked technology-risk demo corpus.

Defines which documents make up the demo cluster, their `document_id`s,
provenance (published vs. mock draft), and the curated baseline edges that
seed the knowledge graph before any LLM-found connections are added. This is
the single source of truth the build pipeline reads from — nothing here is
inferred from filenames.
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
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
# are filled in by a later story once the clause index exists; the graph
# builder is expected to leave them empty here.
CURATED_SEED_EDGES = [
    {
        "source_policy_id": "rmit",
        "target_policy_id": "opres",
        "type": "overlaps",
        "reason": (
            "Both govern the register of critical cloud/third-party services. "
            "RMiT clause 10 (cloud services) overlaps Operational Resilience "
            "6.11 — a change in one can duplicate or contradict the other."
        ),
        "source_clauses": [],
        "target_clauses": [],
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
        "source_clauses": [],
        "target_clauses": [],
        "provenance": "curated",
        "confidence": 1.0,
    },
    {
        "source_policy_id": "rmit",
        "target_policy_id": "bcm",
        "type": "overlaps",
        "reason": (
            "Cloud services supporting critical operations must have "
            "continuity arrangements. RMiT cloud requirements reference "
            "business-continuity expectations in the BCM policy."
        ),
        "source_clauses": [],
        "target_clauses": [],
        "provenance": "curated",
        "confidence": 1.0,
    },
    {
        "source_policy_id": "rmit",
        "target_policy_id": "customer-info",
        "type": "overlaps",
        "reason": (
            "Cloud adoption for critical systems often processes customer data "
            "offshore. RMiT 17.1 (cloud adoption) engages the Management of "
            "Customer Information rules on disclosure and offshore storage of "
            "customer data."
        ),
        "source_clauses": [],
        "target_clauses": [],
        "provenance": "curated",
        "confidence": 1.0,
    },
    {
        "source_policy_id": "opres",
        "target_policy_id": "bcm",
        "type": "overlaps",
        "reason": (
            "Operational resilience and business continuity overlap on "
            "recovery of critical operations after disruption."
        ),
        "source_clauses": [],
        "target_clauses": [],
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
            "Information disclosure requirements."
        ),
        "source_clauses": [],
        "target_clauses": [],
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
