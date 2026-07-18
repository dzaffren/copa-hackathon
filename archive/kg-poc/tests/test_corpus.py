from pathlib import Path

from pipeline.corpus import DOCUMENTS


def test_v1_has_seven_documents():
    assert len(DOCUMENTS) == 7


def test_every_doc_id_appears_in_its_entry():
    for doc_id, entry in DOCUMENTS.items():
        assert entry["doc_id"] == doc_id


def test_every_source_path_points_to_data_corpus():
    # v1 uses the repo's data/corpus/ (relative to the repo root, not kg-poc/).
    for entry in DOCUMENTS.values():
        assert entry["source_path"].parent.name == "corpus"
        assert entry["source_path"].suffix == ".pdf"


def test_all_v1_docs_are_bnm_MY():
    for entry in DOCUMENTS.values():
        assert entry["issuer"] == "BNM"
        assert entry["jurisdiction"] == "MY"


def test_doc_types_are_in_canonical_set():
    canonical = {"PD", "ED", "DP", "BCBS"}
    for entry in DOCUMENTS.values():
        assert entry["doc_type"] in canonical


def test_specific_docs_present():
    expected_ids = {
        "rmit",
        "outsourcing",
        "bcm",
        "opres-dp",
        "recovery-planning",
        "customer-info",
        "open-finance-ed",
    }
    assert set(DOCUMENTS.keys()) == expected_ids
