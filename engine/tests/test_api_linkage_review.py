"""Per-linkage Maker-Checker workflow + Review Queue.

A real audit trail over a single cross-workstream linkage: the AI detects it, a
maker claims and submits it, a (different) checker picks it up and approves,
rejects, or requests changes — every step recorded. The Review Queue is the
aggregate backlog of these across the cross-workstream store.
"""

import json
import shutil

from fastapi.testclient import TestClient

from engine.api import create_app
from engine.config import REPO_ROOT

_EDGE = "x-bcm_pd_2022--rrp_pd_v0_1"
_FINDING = "x-bcm_pd_2022--rrp_pd_v0_1~0"
_CROSS = "_cross"
_MAKER = "fm"  # Farid M.
_CHECKER = "ps"  # Priya S.


def _make_client(tmp_path):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    return TestClient(create_app(workstreams_dir=dst, analyze_delay=0)), dst


def _patch(client, action, actor, comment=None):
    body = {"action": action, "actor_id": actor}
    if comment is not None:
        body["comment"] = comment
    return client.patch(
        f"/api/workstreams/{_CROSS}/edges/{_EDGE}/findings/{_FINDING}/linkage-review",
        json=body,
    )


# --- defaults ---------------------------------------------------------------


def test_a_linkage_defaults_to_ai_detected(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/workstreams/{_CROSS}/edges/{_EDGE}/linkage-review").json()
    first = body["linkages"][0]
    assert first["finding_id"] == _FINDING
    assert first["review"]["status"] == "ai_detected"
    assert first["review"]["maker"] is None
    assert first["review"]["audit"] == []


# --- the happy path ---------------------------------------------------------


def test_full_maker_checker_flow_to_approved(tmp_path):
    client, _ = _make_client(tmp_path)

    claim = _patch(client, "claim", _MAKER).json()["review"]
    assert claim["status"] == "maker_review"
    assert claim["maker"]["id"] == _MAKER
    assert claim["created_at"] is not None

    assert _patch(client, "submit", _MAKER, "Looks like a real overlap").json()[
        "review"
    ]["status"] == "submitted_for_check"

    pick = _patch(client, "pick_up", _CHECKER).json()["review"]
    assert pick["status"] == "checker_review"
    assert pick["checker"]["id"] == _CHECKER

    approved = _patch(client, "approve", _CHECKER, "Confirmed").json()["review"]
    assert approved["status"] == "approved"
    assert approved["checked_at"] is not None

    # Audit trail records every transition, in order, with from/to.
    actions = [a["action"] for a in approved["audit"]]
    assert actions == ["claim", "submit", "pick_up", "approve"]
    assert approved["audit"][0]["from"] == "ai_detected"
    assert approved["audit"][-1]["to"] == "approved"
    # Comments are captured too.
    assert any(c["text"] == "Confirmed" for c in approved["comments"])


def test_request_changes_loops_back_to_the_maker(tmp_path):
    client, _ = _make_client(tmp_path)
    _patch(client, "claim", _MAKER)
    _patch(client, "submit", _MAKER)
    _patch(client, "pick_up", _CHECKER)

    changed = _patch(client, "request_changes", _CHECKER, "Cite 11.11 too").json()[
        "review"
    ]
    assert changed["status"] == "changes_requested"
    # Maker can resubmit from changes_requested.
    assert _patch(client, "submit", _MAKER).json()["review"]["status"] == (
        "submitted_for_check"
    )


# --- the control: a maker cannot check their own work -----------------------


def test_a_maker_cannot_be_the_checker_of_the_same_linkage(tmp_path):
    client, _ = _make_client(tmp_path)
    _patch(client, "claim", _MAKER)
    _patch(client, "submit", _MAKER)
    res = _patch(client, "pick_up", _MAKER)  # same person picks up
    assert res.status_code == 400
    assert res.json()["code"] == "SAME_ACTOR"


# --- state-machine + validation guards --------------------------------------


def test_an_action_not_allowed_from_the_current_status_is_refused(tmp_path):
    client, _ = _make_client(tmp_path)
    res = _patch(client, "approve", _CHECKER)  # nothing to approve yet
    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_WORKFLOW_STATE"


def test_an_unknown_action_is_refused(tmp_path):
    client, _ = _make_client(tmp_path)
    res = _patch(client, "sign_off", _MAKER)
    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_ACTION"


def test_an_unknown_actor_is_refused(tmp_path):
    client, _ = _make_client(tmp_path)
    res = _patch(client, "claim", "nobody")
    assert res.status_code == 400
    assert res.json()["code"] == "UNKNOWN_ACTOR"


def test_a_missing_finding_is_404(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.patch(
        f"/api/workstreams/{_CROSS}/edges/{_EDGE}/findings/{_EDGE}~999/linkage-review",
        json={"action": "claim", "actor_id": _MAKER},
    )
    assert res.status_code == 404
    assert res.json()["code"] == "FINDING_NOT_FOUND"


# --- persistence + queue ----------------------------------------------------


def test_the_state_persists_to_a_sidecar_not_the_findings_file(tmp_path):
    client, dst = _make_client(tmp_path)
    _patch(client, "claim", _MAKER)
    sidecar = dst / _CROSS / "linkage_review" / f"{_EDGE}.json"
    assert sidecar.exists()
    stored = json.loads(sidecar.read_text(encoding="utf-8"))
    assert stored[_FINDING]["status"] == "maker_review"
    # The findings fixture is untouched (no review_state maker-checker leakage).
    findings_file = dst / _CROSS / "findings" / f"{_EDGE}.json"
    raw = json.loads(findings_file.read_text(encoding="utf-8"))
    assert "status" not in raw[0]


def test_review_queue_aggregates_cross_linkages_with_status(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.get("/api/review-queue").json()
    # Both cross pairs' linkages are present (12 + 22).
    assert len(body["items"]) == 34
    # The flagship BCM <-> R&R linkage is attributed correctly.
    flagship = next(it for it in body["items"] if it["edge_id"] == _EDGE)
    assert flagship["near"]["workstream_name"] == "Business Continuity Management"
    assert flagship["far"]["workstream_name"] == "Resolution & Recovery Planning"
    assert flagship["status"] == "ai_detected"
    # Everything starts ai_detected.
    assert body["counts_by_status"]["ai_detected"] == 34


def test_review_queue_reflects_a_transition(tmp_path):
    client, _ = _make_client(tmp_path)
    _patch(client, "claim", _MAKER)
    body = client.get("/api/review-queue").json()
    item = next(it for it in body["items"] if it["finding_id"] == _FINDING)
    assert item["status"] == "maker_review"
    assert item["maker"]["id"] == _MAKER
    assert body["counts_by_status"]["maker_review"] == 1
    assert body["counts_by_status"]["ai_detected"] == 33
