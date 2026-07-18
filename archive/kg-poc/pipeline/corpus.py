"""v1 corpus manifest — 7 BNM regulatory documents from data/corpus/.

Follows the same "single source of truth manifest" pattern as
engine/config.py — the pipeline never infers document identity from
filenames. v2 (remaining 2026 BNM docs) and v3 (BCBS mother-docs) are
tier-two work; see spec §3.
"""

from pathlib import Path
from typing import TypedDict

from pipeline.config import PACKAGE_ROOT

# Corpus lives at the repo root, not under kg-poc/.
REPO_ROOT = PACKAGE_ROOT.parent
CORPUS_DIR = REPO_ROOT / "data" / "corpus"


class DocumentEntry(TypedDict):
    doc_id: str
    source_path: Path
    title: str
    doc_type: str
    jurisdiction: str
    issuer: str
    issued_date: str


DOCUMENTS: dict[str, DocumentEntry] = {
    "rmit": {
        "doc_id": "rmit",
        "source_path": CORPUS_DIR / "pd-rmit-nov25.pdf",
        "title": "Risk Management in Technology (RMiT)",
        "doc_type": "PD",
        "jurisdiction": "MY",
        "issuer": "BNM",
        "issued_date": "2025-11-28",
    },
    "outsourcing": {
        "doc_id": "outsourcing",
        "source_path": CORPUS_DIR / "PD_Outsourcing_20191023.pdf",
        "title": "Outsourcing",
        "doc_type": "PD",
        "jurisdiction": "MY",
        "issuer": "BNM",
        "issued_date": "2019-10-23",
    },
    "bcm": {
        "doc_id": "bcm",
        "source_path": CORPUS_DIR / "PD-BCM.pdf",
        "title": "Business Continuity Management",
        "doc_type": "PD",
        "jurisdiction": "MY",
        "issuer": "BNM",
        "issued_date": "2022-12-19",
    },
    "opres-dp": {
        "doc_id": "opres-dp",
        "source_path": CORPUS_DIR / "dp_operationalresilience_Dec2025.pdf",
        "title": "Operational Resilience (Discussion Paper)",
        "doc_type": "DP",
        "jurisdiction": "MY",
        "issuer": "BNM",
        "issued_date": "2025-12-19",
    },
    "recovery-planning": {
        "doc_id": "recovery-planning",
        "source_path": CORPUS_DIR / "pd_Recovery Planning.pdf",
        "title": "Recovery Planning",
        "doc_type": "PD",
        "jurisdiction": "MY",
        "issuer": "BNM",
        "issued_date": "2021-07-28",
    },
    "customer-info": {
        "doc_id": "customer-info",
        "source_path": CORPUS_DIR / "MCIPD_PD_2025.pdf",
        "title": "Management of Customer Information & Permitted Disclosures",
        "doc_type": "PD",
        "jurisdiction": "MY",
        "issuer": "BNM",
        "issued_date": "2025-10-31",
    },
    "open-finance-ed": {
        "doc_id": "open-finance-ed",
        "source_path": CORPUS_DIR / "ED_Open_Finance_2025.pdf",
        "title": "Open Finance (Exposure Draft)",
        "doc_type": "ED",
        "jurisdiction": "MY",
        "issuer": "BNM",
        "issued_date": "2025-07-01",
    },
}
