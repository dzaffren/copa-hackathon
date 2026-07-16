"""Tests for the Review Linkages routes (GET /review, PATCH review_state).

Each test copies the seeded `data/workstreams/` fixtures into a `tmp_path`, so
the GET tests double as integrity checks on the real demo data while the PATCH
tests mutate only the throwaway copy. No network or credentials — the review
path never touches a model.
"""

import json
import shutil

import pytest
from fastapi.testclient import TestClient

from engine.api import create_app
from engine.config import REPO_ROOT

_OPRES = "opres-v2"
_BCBS_EDGE = "e-opres_v0_3--bcbs_opres_2021"  # seeded, analysed, 3 findings
_FSB_EDGE = "e-opres_v0_3--fsb_3rd_party"  # seeded but NOT analysed (no file)


def _make_client(tmp_path) -> tuple[TestClient, "object"]:
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    return TestClient(create_app(workstreams_dir=dst, analyze_delay=0)), dst


def _review(client, edge=_BCBS_EDGE):
    return client.get(f"/api/workstreams/{_OPRES}/edges/{edge}/review")


# --- GET /review -----------------------------------------------------------


def test_GET_review_returns_edge_nodes_clause_panes_and_findings(tmp_path):
    client, _ = _make_client(tmp_path)
    body = _review(client).json()

    assert body["edge"]["id"] == _BCBS_EDGE
    assert body["edge"]["source_node"]["node_type"] == "task"
    assert body["edge"]["target_node"]["id"] == "bcbs-opres-2021"
    assert len(body["findings"]) == 3
    assert body["counts"] == {"total": 3, "accepted": 0, "dismissed": 0}


def test_GET_review_serves_clause_text_verbatim_from_the_finding(tmp_path):
    """The verbatim guarantee on this path: every pane card's text is the text
    stored on the finding that cites it — never re-parsed, never synthesised."""
    client, _ = _make_client(tmp_path)
    body = _review(client).json()

    cited = {
        c["clause_number"]: c["text"]
        for f in body["findings"]
        for c in f["source_clauses"]
    }
    for card in body["source_clauses"]:
        assert card["text"] == cited[card["clause_number"]]
        assert card["text"], "a pane card must never carry empty clause text"


def test_GET_review_clause_panes_dedupe_by_clause_number(tmp_path):
    client, _ = _make_client(tmp_path)
    body = _review(client).json()
    for side in ("source_clauses", "target_clauses"):
        numbers = [c["clause_number"] for c in body[side]]
        assert len(numbers) == len(set(numbers))


def test_GET_review_findings_default_to_pending_and_carry_derived_ids(tmp_path):
    client, _ = _make_client(tmp_path)
    body = _review(client).json()
    assert [f["review_state"] for f in body["findings"]] == ["pending"] * 3
    assert [f["id"] for f in body["findings"]] == [f"{_BCBS_EDGE}~{i}" for i in range(3)]


def test_GET_review_400_EDGE_NOT_ANALYSED_when_no_findings_file(tmp_path):
    client, _ = _make_client(tmp_path)
    res = _review(client, edge=_FSB_EDGE)
    assert res.status_code == 400
    assert res.json()["code"] == "EDGE_NOT_ANALYSED"


def test_GET_review_404_EDGE_NOT_FOUND_on_unknown_edge(tmp_path):
    client, _ = _make_client(tmp_path)
    res = _review(client, edge="e-nope")
    assert res.status_code == 404
    assert res.json()["code"] == "EDGE_NOT_FOUND"


def test_GET_review_404_WORKSTREAM_NOT_FOUND_on_unknown_workstream(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.get(f"/api/workstreams/nope/edges/{_BCBS_EDGE}/review")
    assert res.status_code == 404
    assert res.json()["code"] == "WORKSTREAM_NOT_FOUND"


# --- PATCH review_state ----------------------------------------------------


def _patch(client, finding_id, state, edge=_BCBS_EDGE):
    return client.patch(
        f"/api/workstreams/{_OPRES}/edges/{edge}/findings/{finding_id}",
        json={"review_state": state},
    )


@pytest.mark.parametrize("state", ["accepted", "dismissed", "pending"])
def test_PATCH_review_state_persists_to_disk(tmp_path, state):
    client, dst = _make_client(tmp_path)
    target = f"{_BCBS_EDGE}~0"

    res = _patch(client, target, state)
    assert res.status_code == 200
    assert res.json()["finding"]["review_state"] == state

    on_disk = json.loads(
        (dst / _OPRES / "findings" / f"{_BCBS_EDGE}.json").read_text(encoding="utf-8")
    )
    assert on_disk[0]["review_state"] == state
    # A re-read through the API agrees with disk.
    assert _review(client).json()["findings"][0]["review_state"] == state


def test_PATCH_review_state_is_idempotent(tmp_path):
    client, _ = _make_client(tmp_path)
    target = f"{_BCBS_EDGE}~1"
    first = _patch(client, target, "accepted").json()
    second = _patch(client, target, "accepted").json()
    assert first == second


def test_PATCH_review_state_updates_header_counts(tmp_path):
    client, _ = _make_client(tmp_path)
    _patch(client, f"{_BCBS_EDGE}~0", "accepted")
    body = _patch(client, f"{_BCBS_EDGE}~1", "dismissed").json()
    assert body["counts"] == {"total": 3, "accepted": 1, "dismissed": 1}


def test_PATCH_reopen_restores_pending_and_clears_the_count(tmp_path):
    client, _ = _make_client(tmp_path)
    target = f"{_BCBS_EDGE}~2"
    _patch(client, target, "dismissed")
    body = _patch(client, target, "pending").json()
    assert body["finding"]["review_state"] == "pending"
    assert body["counts"]["dismissed"] == 0


def test_PATCH_never_deletes_a_finding(tmp_path):
    """Dismiss is a state, not a deletion — the record stays readable."""
    client, _ = _make_client(tmp_path)
    _patch(client, f"{_BCBS_EDGE}~0", "dismissed")
    body = _review(client).json()
    assert len(body["findings"]) == 3
    assert body["findings"][0]["source_clauses"], "clause citations survive dismissal"


def test_PATCH_400_INVALID_REVIEW_STATE_on_unknown_state(tmp_path):
    client, _ = _make_client(tmp_path)
    res = _patch(client, f"{_BCBS_EDGE}~0", "approved")
    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_REVIEW_STATE"


def test_PATCH_404_FINDING_NOT_FOUND_on_unknown_finding(tmp_path):
    client, _ = _make_client(tmp_path)
    res = _patch(client, f"{_BCBS_EDGE}~99", "accepted")
    assert res.status_code == 404
    assert res.json()["code"] == "FINDING_NOT_FOUND"


def test_PATCH_400_EDGE_NOT_ANALYSED_on_edge_without_findings(tmp_path):
    client, _ = _make_client(tmp_path)
    res = _patch(client, f"{_FSB_EDGE}~0", "accepted", edge=_FSB_EDGE)
    assert res.status_code == 400
    assert res.json()["code"] == "EDGE_NOT_ANALYSED"


def test_PATCH_does_not_disturb_the_other_findings(tmp_path):
    client, _ = _make_client(tmp_path)
    before = _review(client).json()["findings"]
    _patch(client, f"{_BCBS_EDGE}~1", "dismissed")
    after = _review(client).json()["findings"]
    for i in (0, 2):
        assert after[i] == before[i]
