"""Review state over a per-edge findings file (Review Linkages screen).

The findings fixtures are a bare JSON list of finding objects, each carrying its
own verbatim `source_clauses` / `target_clauses` (`{clause_number, text}`). That
embedded text is the verbatim-citation guarantee on this path: the review screen
quotes clauses straight from the finding, never from a re-parse, so a finding can
never cite text its own record does not contain.

Two fields the fixtures do not carry are needed to review a finding — a stable
`id` and a `review_state`. Rather than migrate the fixtures (and force every
existing finding to be rewritten), both are **derived on read**:

- `id` is the edge id plus the finding's index (`{edge_id}~{i}`). Stable for a
  given file, and no fixture edit is needed to introduce it. See `finding_id`
  for why the separator is `~` and must stay that way.
- `review_state` defaults to `"pending"` when absent.

A write persists the full list back with `review_state` materialised, so the
first accept/dismiss on an edge is what introduces the field to disk. Findings
are never deleted — dismiss is a state.
"""

import json
from pathlib import Path
from typing import Any, Literal, Optional

ReviewState = Literal["pending", "accepted", "dismissed"]

REVIEW_STATES: frozenset[str] = frozenset({"pending", "accepted", "dismissed"})

_DEFAULT_STATE: ReviewState = "pending"


class FindingsNotAnalysedError(Exception):
    """The edge has no findings file — it has not been analysed yet."""


class FindingNotFoundError(Exception):
    """No finding on this edge carries the given id."""


def findings_path(workstreams_dir: Path, workstream_id: str, edge_id: str) -> Path:
    return workstreams_dir / workstream_id / "findings" / f"{edge_id}.json"


def finding_id(edge_id: str, index: int) -> str:
    """Derive a finding's stable id from its edge and position.

    The fixtures carry no id. Index-based derivation is stable because findings
    are only ever appended or state-changed, never reordered or deleted on disk
    (the "dismissed sorts to the bottom" rule is a view concern, applied in the
    UI — the file order is the creation order).

    The separator is `~`, which RFC 3986 lists as *unreserved* and so survives a
    URL path segment untouched. It is not cosmetic: the id travels as a path
    param on PATCH, and a `#` here silently truncates the URL into a fragment,
    404-ing every write.
    """
    return f"{edge_id}~{index}"


def load(workstreams_dir: Path, workstream_id: str, edge_id: str) -> list[dict[str, Any]]:
    """Read an edge's findings, deriving `id` and defaulting `review_state`.

    Raises FindingsNotAnalysedError when the file is absent — an unanalysed edge
    is a different condition from an analysed edge with zero findings, and the
    route reports them differently.
    """
    path = findings_path(workstreams_dir, workstream_id, edge_id)
    if not path.exists():
        raise FindingsNotAnalysedError(edge_id)
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        {
            **finding,
            "id": finding.get("id") or finding_id(edge_id, i),
            "review_state": finding.get("review_state", _DEFAULT_STATE),
        }
        for i, finding in enumerate(raw)
    ]


def save(
    workstreams_dir: Path,
    workstream_id: str,
    edge_id: str,
    findings: list[dict[str, Any]],
) -> None:
    """Persist the full findings list. UTF-8 always — clause text carries
    Unicode (§, en-dashes, U+2212); the platform default mangles it on Windows.
    """
    path = findings_path(workstreams_dir, workstream_id, edge_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(findings, indent=2, ensure_ascii=False), encoding="utf-8")


def set_review_state(
    workstreams_dir: Path,
    workstream_id: str,
    edge_id: str,
    target_id: str,
    state: ReviewState,
) -> dict[str, Any]:
    """Set one finding's review_state and persist. Idempotent.

    Returns the updated finding. Raises FindingNotFoundError if `target_id` is
    not on this edge, FindingsNotAnalysedError if the edge has no findings file.
    """
    findings = load(workstreams_dir, workstream_id, edge_id)
    updated: Optional[dict[str, Any]] = None
    for finding in findings:
        if finding["id"] == target_id:
            finding["review_state"] = state
            updated = finding
            break
    if updated is None:
        raise FindingNotFoundError(target_id)
    save(workstreams_dir, workstream_id, edge_id, findings)
    return updated


def counts(findings: list[dict[str, Any]]) -> dict[str, int]:
    """Header counts: total / accepted / dismissed (pending is the remainder)."""
    return {
        "total": len(findings),
        "accepted": sum(1 for f in findings if f["review_state"] == "accepted"),
        "dismissed": sum(1 for f in findings if f["review_state"] == "dismissed"),
    }
