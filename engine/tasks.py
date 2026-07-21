"""Task workflow status (Maker-Checker), persisted per task node.

`AssignDialog.tsx`/`TaskScreenPage.tsx` used to mock Draft -> Pending Review as
local React state only ("MVP1 does not persist the assignment"). This module
is the same derive-on-read + write-through pattern `engine/findings.py` uses
for finding review state, applied to a task's workflow status: a side-file per
task, written once a maker actually assigns a checker or a checker approves,
absent otherwise.

There is no separate reviewer/approver persona in this MVP (CLAUDE.md) — the
person recorded as `checker` when a task moves to Pending Review is the same
person recorded as `approved_by` if the task later moves to Approved. That is
a known, documented simplification, not an oversight.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

WorkflowState = Literal["draft", "pending_review", "approved"]

WORKFLOW_STATES: frozenset[str] = frozenset({"draft", "pending_review", "approved"})

_DEFAULT_STATE: WorkflowState = "draft"


def workflow_path(workstreams_dir: Path, workstream_id: str, node_id: str) -> Path:
    return workstreams_dir / workstream_id / "task_workflow" / f"{node_id}.json"


def _default_status(node_status: Optional[str]) -> WorkflowState:
    """The workflow's starting point when nobody has ever assigned or approved
    this task — derived from the node's own on-disk `status` field, absorbing
    the mapping `TaskScreenPage.tsx`'s `initialStatus()` used to duplicate
    client-side."""
    if node_status == "approved":
        return "approved"
    if node_status == "pending_review":
        return "pending_review"
    return _DEFAULT_STATE


def load_workflow(
    workstreams_dir: Path,
    workstream_id: str,
    node_id: str,
    node_status: Optional[str],
) -> dict[str, Any]:
    """A task's live workflow state.

    Falls back to a status derived from the node's own `status` field when no
    workflow file exists yet — the same graceful-absence behaviour
    `findings.load` has for an unanalysed edge, just returning a default
    instead of raising (a task always has *some* workflow state; an edge
    genuinely may never have been analysed).
    """
    path = workflow_path(workstreams_dir, workstream_id, node_id)
    if not path.exists():
        return {
            "status": _default_status(node_status),
            "checker": None,
            "approved_by": None,
            "approved_at": None,
        }
    return json.loads(path.read_text(encoding="utf-8"))


def set_workflow(
    workstreams_dir: Path,
    workstream_id: str,
    node_id: str,
    node_status: Optional[str],
    status: WorkflowState,
    actor: dict[str, Any],
) -> dict[str, Any]:
    """Set a task's workflow status and persist it. Idempotent.

    Moving to `pending_review` records `actor` as the checker; moving to
    `approved` records `actor` as who approved and stamps `approved_at`.
    """
    workflow = load_workflow(workstreams_dir, workstream_id, node_id, node_status)
    workflow["status"] = status
    if status == "pending_review":
        workflow["checker"] = actor
    elif status == "approved":
        workflow["approved_by"] = actor
        workflow["approved_at"] = (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )

    path = workflow_path(workstreams_dir, workstream_id, node_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(workflow, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return workflow
