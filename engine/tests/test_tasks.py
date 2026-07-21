"""Tests for engine.tasks — persisted Maker-Checker workflow state."""

import json

from engine import tasks


def test_load_workflow_defaults_from_node_status_when_no_file_exists(tmp_path):
    assert tasks.load_workflow(tmp_path, "ws", "node-a", None) == {
        "status": "draft",
        "checker": None,
        "approved_by": None,
        "approved_at": None,
    }
    assert tasks.load_workflow(tmp_path, "ws", "node-a", "pending_review")["status"] == (
        "pending_review"
    )
    assert tasks.load_workflow(tmp_path, "ws", "node-a", "approved")["status"] == "approved"


def test_set_workflow_to_pending_review_records_the_checker(tmp_path):
    checker = {"id": "fm", "name": "Farid M."}
    workflow = tasks.set_workflow(
        tmp_path, "ws", "node-a", "in_progress", "pending_review", checker
    )
    assert workflow["status"] == "pending_review"
    assert workflow["checker"] == checker
    assert workflow["approved_by"] is None

    # Persisted — a fresh load (no node_status fallback needed) sees it too.
    reloaded = tasks.load_workflow(tmp_path, "ws", "node-a", "in_progress")
    assert reloaded == workflow


def test_set_workflow_to_approved_records_who_and_when(tmp_path):
    checker = {"id": "fm", "name": "Farid M."}
    tasks.set_workflow(tmp_path, "ws", "node-a", "in_progress", "pending_review", checker)
    approved = tasks.set_workflow(
        tmp_path, "ws", "node-a", "in_progress", "approved", checker
    )
    assert approved["status"] == "approved"
    assert approved["approved_by"] == checker
    assert approved["approved_at"] is not None
    # The checker recorded earlier is not erased by the later transition.
    assert approved["checker"] == checker


def test_set_workflow_persists_utf8(tmp_path):
    tasks.set_workflow(
        tmp_path, "ws", "node-a", "in_progress", "pending_review", {"id": "ps", "name": "Priya S."}
    )
    path = tasks.workflow_path(tmp_path, "ws", "node-a")
    assert json.loads(path.read_text(encoding="utf-8"))["checker"]["name"] == "Priya S."
