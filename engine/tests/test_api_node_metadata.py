"""Node-detail regulatory metadata: legal basis, ISMP classification, and the
supervisory-letter document type.

Phase 2 surfaces `legal_basis` and `ismp_classification` (added to the concept
sidecar) through the node-detail route, and confirms the supervisory-letter node
type is first-class end to end.
"""

import shutil

from fastapi.testclient import TestClient

from engine.api import create_app
from engine.config import REPO_ROOT


def _make_client(tmp_path):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    return TestClient(create_app(workstreams_dir=dst, analyze_delay=0)), dst


def test_supervisory_letter_is_a_first_class_node_type_with_a_profile(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.get(
        "/api/workstreams/rmit-v2-2025/nodes/bnm-supervisory-letter-rmit-2025"
    ).json()
    assert body["node_type"] == "supervisory-letter"
    concepts = body["concepts"]
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
        concepts = client.get(f"/api/workstreams/{ws}/nodes/{node}").json()["concepts"]
        assert concepts["status"] == "available"
        assert "legal_basis" in concepts
        assert "ismp_classification" in concepts
