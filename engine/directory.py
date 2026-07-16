"""The static colleague directory (MVP1).

There is no staff directory integration and no auth. The tool has exactly one
user — Aisyah R., the policy drafter persona — and a short list of colleagues she
can nominate as reviewers. Both are hard-coded here so the demo needs no
identity provider.

Names match the personas already seeded across `data/workstreams/`: Aisyah owns
the OpRes workstream, Farid and Priya review it. Jarod is directory-only — he
appears in the reviewer picker but owns nothing, which keeps the picker from
looking like a mirror of the workstream list.
"""

from typing import Any, Optional

# Every person the reviewer picker can offer, including the owner.
PEOPLE: list[dict[str, str]] = [
    {"id": "ar", "name": "Aisyah R."},
    {"id": "fm", "name": "Farid M."},
    {"id": "ps", "name": "Priya S."},
    {"id": "jn", "name": "Jarod N."},
]

# The hard-coded MVP1 user. Owner of anything they create; never selectable as a
# reviewer of their own workstream.
OWNER_ID: str = "ar"

_BY_ID: dict[str, dict[str, str]] = {p["id"]: p for p in PEOPLE}


def person(person_id: str) -> Optional[dict[str, str]]:
    """The `{id, name}` for a directory id, or None when unknown."""
    found = _BY_ID.get(person_id)
    return dict(found) if found else None


def owner() -> dict[str, str]:
    """The current user, as an `{id, name}` record."""
    return dict(_BY_ID[OWNER_ID])


def selectable_reviewers() -> list[dict[str, str]]:
    """Everyone the current user may nominate — the directory minus themselves.

    A drafter reviewing their own draft is the failure the reviewer field exists
    to prevent, so the owner is excluded here rather than filtered in the UI:
    the picker cannot offer what the API does not return.
    """
    return [dict(p) for p in PEOPLE if p["id"] != OWNER_ID]


def resolve_reviewers(reviewer_ids: Any) -> tuple[Optional[list[dict[str, str]]], Optional[str]]:
    """Resolve ids to `{id, name}` records, preserving order and dropping dupes.

    Returns `(reviewers, None)` on success, or `(None, bad_id)` naming the first
    id that is not in the directory or is the owner. Selecting yourself is
    rejected rather than silently ignored — a request that says "review your own
    work" is a mistake worth reporting.
    """
    if reviewer_ids is None:
        return [], None
    if not isinstance(reviewer_ids, list):
        return None, repr(reviewer_ids)
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for rid in reviewer_ids:
        if not isinstance(rid, str) or rid not in _BY_ID or rid == OWNER_ID:
            return None, str(rid)
        if rid in seen:
            continue
        seen.add(rid)
        out.append(dict(_BY_ID[rid]))
    return out, None
