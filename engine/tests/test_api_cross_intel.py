"""Cross-Workstream Intelligence API — the relationship-detail endpoint and the
intel enrichment on the cross-links list routes.

The flagship scenario is BCM (Business Continuity Management) vs Resolution &
Recovery Planning: two BNM workstreams drafted in parallel that overlap on
continuity of critical functions. The point of the intelligence surface is that
this overlap is explainable — shared legal basis, shared applicability, shared
topics — and traceable to verbatim clause evidence on both sides.
"""

import shutil

from fastapi.testclient import TestClient

from engine.api import create_app
from engine.config import REPO_ROOT

_BCM_RRP = "x-bcm_pd_2022--rrp_pd_v0_1"
_OPRES_OF = "x-open_finance_ed--opres_dp_2025"


def _make_client(tmp_path):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    return TestClient(create_app(workstreams_dir=dst, analyze_delay=0)), dst


# --- the flagship relationship is attributed correctly ----------------------


def test_bcm_link_is_homed_to_the_bcm_workstream_not_open_finance(tmp_path):
    """BCM was previously parked under open-finance-ed, so the flagship overlap
    mis-rendered as "Open Finance <-> Resolution & Recovery". It now reads as
    the real story: Business Continuity Management <-> Resolution & Recovery."""
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/cross-links/{_BCM_RRP}").json()
    assert body["near"]["workstream_id"] == "bcm"
    assert body["near"]["workstream_name"] == "Business Continuity Management"
    assert body["far"]["workstream_id"] == "resolution-recovery"


def test_bcm_workstream_is_now_listed_and_first_class(tmp_path):
    client, _ = _make_client(tmp_path)
    listed = {w["id"] for w in client.get("/api/workstreams").json()["workstreams"]}
    assert "bcm" in listed
    graph = client.get("/api/workstreams/bcm/graph").json()
    assert graph["primary_task_id"] == "bcm-pd-2022"


# --- the relationship is explainable ----------------------------------------


def test_detail_explains_why_the_overlap_was_detected(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/cross-links/{_BCM_RRP}").json()
    shared = body["shared_attributes"]
    assert "FSA 2013" in shared["legal_basis"] and "IFSA 2013" in shared["legal_basis"]
    assert "continuity of critical functions" in shared["keywords"]
    assert any("licensed" in a.lower() for a in shared["applicability"])
    # reasons render those shared facts as plain language
    assert any("issued under FSA 2013" in r for r in body["reasons"])
    assert any("apply to" in r for r in body["reasons"])


def test_detail_classifies_bcm_rrp_as_divergent_not_conflict(tmp_path):
    """The BCM/RRP linkages differ on timelines but do not genuinely conflict —
    the classification must not overstate that."""
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/cross-links/{_BCM_RRP}").json()
    assert body["classification"] == "divergent"
    assert body["risk_level"] == "medium"


def test_detail_carries_verbatim_clause_evidence(tmp_path):
    """Every linkage cites at least one clause, and every citation carries a
    verbatim number + text. One `goes-beyond` linkage legitimately has evidence
    on only its own side (BCM goes beyond with nothing to point at on the RRP
    side) — so evidence is required overall, not on both sides of every finding.
    """
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/cross-links/{_BCM_RRP}").json()
    assert len(body["findings"]) > 0
    for finding in body["findings"]:
        clauses = finding["source_clauses"] + finding["target_clauses"]
        assert clauses, f"linkage with no evidence at all: {finding['summary'][:40]}"
        for clause in clauses:
            assert clause["clause_number"] and clause["text"].strip()


def test_detail_includes_both_regulatory_profiles(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/cross-links/{_BCM_RRP}").json()
    assert body["near"]["concepts"]["status"] == "available"
    assert body["near"]["concepts"]["policy_owner"] == "Jarod N."
    assert body["far"]["concepts"]["policy_owner"] == "Priya S."
    assert "DFIA 2002" in body["near"]["concepts"]["legal_basis"]


def test_detail_404_for_unknown_link(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.get("/api/cross-links/nope")
    assert res.status_code == 404
    assert res.json()["code"] == "CROSS_LINK_NOT_FOUND"


# --- list routes carry the same intel enrichment ----------------------------


def test_aggregate_list_carries_classification_and_detection_date(tmp_path):
    client, _ = _make_client(tmp_path)
    links = {ln["id"]: ln for ln in client.get("/api/cross-links").json()["links"]}
    assert links[_OPRES_OF]["detected_at"] == "2026-07-11"
    assert links[_BCM_RRP]["classification"] == "divergent"
    assert links[_BCM_RRP]["risk_level"] == "medium"
    assert "reasons" in links[_BCM_RRP]


def test_per_workstream_list_carries_intel_from_the_asking_end(tmp_path):
    client, _ = _make_client(tmp_path)
    links = client.get("/api/workstreams/resolution-recovery/cross-links").json()["links"]
    assert len(links) == 1
    assert links[0]["classification"] == "divergent"
    assert links[0]["far"]["workstream_name"] == "Business Continuity Management"


def test_ismp_is_supported_but_never_claimed_shared_today(tmp_path):
    """The field is honoured end-to-end; because no offline source exists it is
    null on both sides, so a shared-ISMP claim never fires."""
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/cross-links/{_BCM_RRP}").json()
    assert body["shared_attributes"]["ismp_classification"] is None
    assert body["near"]["concepts"]["ismp_classification"] is None
