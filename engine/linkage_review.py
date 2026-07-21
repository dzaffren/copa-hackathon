"""Per-linkage Maker-Checker workflow with an append-only audit trail.

The task-level workflow (`engine/tasks.py`) governs a whole draft; this governs a
single AI-detected linkage (a finding on an edge), which is what Cross-Workstream
Intelligence surfaces. It is the same derive-on-read + write-through, side-file
pattern (`findings.py`, `tasks.py`): a per-edge file
`{workstream}/linkage_review/{edge_id}.json` keyed by finding id, written the
first time anyone acts on a linkage, absent (and defaulted) otherwise. It never
mutates the finding fixtures, so the verbatim clause evidence is untouched.

The seven statuses model the real institutional flow:

    ai_detected --claim--> maker_review --submit--> submitted_for_check
      --pick_up--> checker_review --approve---->  approved   (terminal)
                                  --reject----->  rejected   (terminal)
                                  --request_changes--> changes_requested
    changes_requested --submit--> submitted_for_check   (rework loop)

Every transition appends to `audit` — actor, action, from→to, timestamp, and an
optional comment — so the record is a genuine audit trail, not a status flag.
A checker may not be the maker of the same linkage (the whole point of the
control); that is enforced, not left to the UI.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

LinkageStatus = Literal[
    "ai_detected",
    "maker_review",
    "submitted_for_check",
    "checker_review",
    "approved",
    "rejected",
    "changes_requested",
]

LINKAGE_STATUSES: frozenset[str] = frozenset(
    {
        "ai_detected",
        "maker_review",
        "submitted_for_check",
        "checker_review",
        "approved",
        "rejected",
        "changes_requested",
    }
)

_DEFAULT_STATUS: LinkageStatus = "ai_detected"

# action -> allowed source statuses, resulting status, and which role the actor
# takes. `role` drives who gets recorded (maker vs checker) and the same-actor
# guard on the checker side.
TRANSITIONS: dict[str, dict[str, Any]] = {
    "claim": {"from": frozenset({"ai_detected"}), "to": "maker_review", "role": "maker"},
    "submit": {
        "from": frozenset({"maker_review", "changes_requested"}),
        "to": "submitted_for_check",
        "role": "maker",
    },
    "pick_up": {
        "from": frozenset({"submitted_for_check"}),
        "to": "checker_review",
        "role": "checker",
    },
    "approve": {"from": frozenset({"checker_review"}), "to": "approved", "role": "checker"},
    "reject": {"from": frozenset({"checker_review"}), "to": "rejected", "role": "checker"},
    "request_changes": {
        "from": frozenset({"checker_review"}),
        "to": "changes_requested",
        "role": "checker",
    },
}

ACTIONS: frozenset[str] = frozenset(TRANSITIONS)


class LinkageReviewError(Exception):
    """A maker-checker transition was refused. Carries a stable `code` and a
    human message so the API can map it to a 400 without a second lookup."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def linkage_review_path(workstreams_dir: Path, workstream_id: str, edge_id: str) -> Path:
    return workstreams_dir / workstream_id / "linkage_review" / f"{edge_id}.json"


def default_record() -> dict[str, Any]:
    """A linkage nobody has acted on yet: the AI found it, and it awaits a maker."""
    return {
        "status": _DEFAULT_STATUS,
        "maker": None,
        "checker": None,
        "created_at": None,
        "checked_at": None,
        "comments": [],
        "audit": [],
    }


def load_edge(
    workstreams_dir: Path, workstream_id: str, edge_id: str
) -> dict[str, dict[str, Any]]:
    """The `{finding_id: record}` map for an edge, or `{}` when none acted on."""
    path = linkage_review_path(workstreams_dir, workstream_id, edge_id)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def record_for(
    workstreams_dir: Path, workstream_id: str, edge_id: str, finding_id: str
) -> dict[str, Any]:
    """One linkage's record, defaulted (ai_detected) when it has never been touched."""
    return load_edge(workstreams_dir, workstream_id, edge_id).get(
        finding_id, default_record()
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def apply_action(
    workstreams_dir: Path,
    workstream_id: str,
    edge_id: str,
    finding_id: str,
    action: str,
    actor: dict[str, Any],
    comment: Optional[str] = None,
) -> dict[str, Any]:
    """Apply a maker-checker `action` by `actor` to one linkage, and persist.

    Records the role side-effects (maker on claim, checker on pick_up), stamps
    the timestamps, appends any `comment`, and appends the audit entry. Raises
    `LinkageReviewError` (with a stable code) when the action is unknown, not
    allowed from the current status, or would let a maker check their own work.
    """
    if action not in TRANSITIONS:
        raise LinkageReviewError("INVALID_ACTION", f"Unknown action '{action}'")
    transition = TRANSITIONS[action]

    edge_records = load_edge(workstreams_dir, workstream_id, edge_id)
    record = edge_records.get(finding_id) or default_record()
    current = record["status"]
    if current not in transition["from"]:
        raise LinkageReviewError(
            "INVALID_WORKFLOW_STATE",
            f"Action '{action}' is not allowed from status '{current}'",
        )

    # Role side-effects + the same-actor guard (a checker cannot be the maker).
    if transition["role"] == "maker" and action == "claim":
        record["maker"] = actor
        record["created_at"] = _now()
    elif transition["role"] == "checker" and action == "pick_up":
        maker = record.get("maker")
        if maker and maker.get("id") == actor.get("id"):
            raise LinkageReviewError(
                "SAME_ACTOR", "The checker of a linkage cannot be its maker"
            )
        record["checker"] = actor

    to_status = transition["to"]
    if to_status in ("approved", "rejected"):
        record["checked_at"] = _now()

    at = _now()
    if comment:
        record["comments"].append({"author": actor, "at": at, "text": comment})
    record["audit"].append(
        {
            "actor": actor,
            "action": action,
            "from": current,
            "to": to_status,
            "at": at,
            "comment": comment,
        }
    )
    record["status"] = to_status

    edge_records[finding_id] = record
    path = linkage_review_path(workstreams_dir, workstream_id, edge_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(edge_records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return record


# Statuses that still need a human somewhere in the loop — the Review Queue's
# working set. Approved and rejected are done; everything else is outstanding.
OPEN_STATUSES: frozenset[str] = LINKAGE_STATUSES - {"approved", "rejected"}


def counts_by_status(records: list[dict[str, Any]]) -> dict[str, int]:
    """Tally a set of linkage records by status, for the queue's header."""
    tally: dict[str, int] = {s: 0 for s in LINKAGE_STATUSES}
    for record in records:
        status = record.get("status", _DEFAULT_STATUS)
        tally[status] = tally.get(status, 0) + 1
    return tally
