"""Node-detail regulatory metadata: legal basis, ISMP classification, the
supervisory-letter document type, and the drafter's own edits to the profile.

Phase 2 surfaces `legal_basis` and `ismp_classification` (added to the concept
sidecar) through the node-detail route, and confirms the supervisory-letter node
type is first-class end to end.

The write side (`PUT .../nodes/{node_id}/metadata`) lets the drafter record what
she knows about any document in any workstream. It is a full replacement of the
nine-field profile, not a patch, and every rejection happens before any
filesystem write.
"""

import json
import shutil

from fastapi.testclient import TestClient

from engine.api import create_app
from engine.concepts import CONCEPT_FIELDS, concepts_path
from engine.config import REPO_ROOT


def _make_client(tmp_path):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    return TestClient(create_app(workstreams_dir=dst)), dst


def _metadata_url(workstream_id, node_id):
    return f"/api/workstreams/{workstream_id}/nodes/{node_id}/metadata"


def test_supervisory_letter_is_a_first_class_node_type_with_a_profile(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.get(
        "/api/workstreams/rmit-v2-2025/nodes/bnm-supervisory-letter-rmit-2025"
    ).json()
    assert body["node_type"] == "supervisory-letter"
    # The nine-field regulatory profile now lands under `metadata`; `concepts`
    # carries extracted axes.
    concepts = body["metadata"]
    assert concepts["status"] == "available"
    assert "RMiT" in concepts["keywords"]
    assert concepts["applicability"].startswith("Financial institutions")
    # An honest profile: no invented legal basis or classification for a letter.
    assert concepts["legal_basis"] is None
    assert concepts["ismp_classification"] is None


def test_new_concept_fields_are_present_for_every_enriched_document(tmp_path):
    """legal_basis + ismp_classification round-trip through save/load for the
    documents enriched in Phase 1/2, so the intelligence layer can rely on them."""
    client, _ = _make_client(tmp_path)
    for ws, node in [
        ("open-finance-ed", "of-ed-2025"),
        ("opres-v2", "opres-pd-v0-3"),
    ]:
        concepts = client.get(f"/api/workstreams/{ws}/nodes/{node}").json()["metadata"]
        assert concepts["status"] == "available"
        assert "legal_basis" in concepts
        assert "ismp_classification" in concepts


def test_a_first_save_creates_the_side_file(tmp_path):
    """Test 1: a node nobody prepared has no side-file; the first save makes one.

    Absence is the ordinary case, not an error — the drafter opens a document
    with an empty profile and fills in the two fields she is confident about.
    """
    client, workstreams_dir = _make_client(tmp_path)
    path = concepts_path(workstreams_dir, "open-finance-pd-2026", "bis-papers-168")
    assert not path.exists()

    response = client.put(
        _metadata_url("open-finance-pd-2026", "bis-papers-168"),
        json={
            "policy_owner": "Priya S.",
            "applicability": None,
            "empowerment_framework": None,
            "requirement": None,
            "issuance_date": None,
            "effective_date": None,
            "keywords": ["operational resilience"],
            "legal_basis": None,
            "ismp_classification": None,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["node_id"] == "bis-papers-168"
    assert body["metadata"]["status"] == "available"
    assert body["metadata"]["policy_owner"] == "Priya S."
    assert body["metadata"]["keywords"] == ["operational resilience"]

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert list(saved) == list(CONCEPT_FIELDS)
    assert sum(1 for value in saved.values() if value is None) == 7


def test_a_save_overwrites_an_existing_profile_whole(tmp_path):
    """Test 2: a save is a full replacement, not a patch.

    Deliberate: the form always sends all nine fields, so a field absent from the
    body is one the drafter cleared — leaving the stored value in place would show
    her something she had just deleted.

    The fixture's `rmit-pd-v2` profile carries only `policy_owner`, so this fills
    it out first; a replacement is only observable against a populated profile.
    """
    client, workstreams_dir = _make_client(tmp_path)
    path = concepts_path(workstreams_dir, "rmit-v2-2025", "rmit-pd-v2")
    assert json.loads(path.read_text(encoding="utf-8"))["policy_owner"] == "Aisyah R."

    populated = client.put(
        _metadata_url("rmit-v2-2025", "rmit-pd-v2"),
        json={
            "policy_owner": "Aisyah R.",
            "applicability": "Licensed banks.",
            "empowerment_framework": "Issued pursuant to section 143(2) of the FSA 2013.",
            "requirement": "Maintain technology risk controls.",
            "issuance_date": "28 November 2025",
            "effective_date": "28 November 2025",
            "keywords": ["technology risk", "cloud"],
            "legal_basis": ["FSA 2013"],
            "ismp_classification": "Prudential",
        },
    )
    assert populated.status_code == 200
    assert all(value is not None for value in populated.json()["metadata"].values())

    response = client.put(
        _metadata_url("rmit-v2-2025", "rmit-pd-v2"),
        json={"policy_owner": "Farid M."},
    )

    assert response.status_code == 200
    metadata = response.json()["metadata"]
    assert metadata["policy_owner"] == "Farid M."
    assert [metadata[field] for field in CONCEPT_FIELDS if field != "policy_owner"] == [
        None
    ] * 8
