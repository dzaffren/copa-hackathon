"""Per-node concept metadata (the Node Detail panel's Concepts disclosure).

The node-detail route has always rendered a "Concepts" section with a fixed
placeholder — `{"status": "placeholder", "message": "Concept extraction not
enabled in MVP1"}` — because nothing populated it. This module is the read
side of the fix: a per-node side-file, written offline by
`scripts/enrich_node_metadata.py`, mirroring the `findings/{edge_id}.json`
convention (`engine/findings.py`) so `graph.json` diffs stay small and
reviewable.

Absence is the common, expected case — most nodes have not been enriched, and
that is not an error. `load_concepts` returns `None` in that case, and the
caller falls back to the placeholder exactly like an unanalysed edge falls
back to "not analysed" rather than erroring (`findings.FindingsNotAnalysedError`).

Every field here is either a verbatim quote from a clause the node's own
document contains, or a value already carried structurally on the node
(`owner`) — never invented. A field the enrichment script could not honestly
derive is `null`, not guessed.
"""

import json
from pathlib import Path
from typing import Any, Optional

# The regulatory-profile concept fields. The first seven are the original set;
# `legal_basis` and `ismp_classification` were added for Cross-Workstream
# Intelligence, where a *shared* Act or classification is one of the strongest
# early signals that two workstreams overlap. Both are additive — a node whose
# side-file omits them still loads (missing keys read back as `None`).
#
# Honesty rules (unchanged): every populated value is either a verbatim clause
# quote from the node's own document (`empowerment_framework`), a value already
# carried structurally on the node (`policy_owner`, `issuance_date`), or a
# structured reference already documented elsewhere in the corpus
# (`legal_basis` — the same kind of value `pursuant_to` already holds on a
# node). A field that cannot be honestly derived is `null`, not guessed.
# `ismp_classification` in particular has NO offline source (its authority is
# CAS's RH publication form, which the repo does not hold) and is therefore
# `null` everywhere today — the field exists so the UI can render "pending"
# rather than hide the concept.
CONCEPT_FIELDS: tuple[str, ...] = (
    "policy_owner",
    "applicability",
    "empowerment_framework",
    "requirement",
    "issuance_date",
    "effective_date",
    "keywords",
    "legal_basis",
    "ismp_classification",
)


# The two list-valued fields. Both hold several short values (topic keywords,
# Acts) and both tolerate a bare string, because side-files written before the
# panel rendered chips carry scalars.
LIST_FIELDS: frozenset[str] = frozenset({"keywords", "legal_basis"})

# 2000 characters per scalar field. `empowerment_framework` holds a whole
# statutory-basis clause quoted word-for-word, which is the longest thing any of
# these fields legitimately carries, so this is generous rather than tight.
MAX_FIELD_CHARS: int = 2000

# A profile lists topics and Acts, not a corpus: 50 chips is far past what a
# drafter would type, and past it the panel would be unreadable anyway.
MAX_LIST_MEMBERS: int = 50

# Each chip is a keyword or an Act's short name — a phrase, never a sentence.
MAX_LIST_MEMBER_CHARS: int = 200


def concepts_path(workstreams_dir: Path, workstream_id: str, node_id: str) -> Path:
    return workstreams_dir / workstream_id / "concepts" / f"{node_id}.json"


def load_concepts(
    workstreams_dir: Path, workstream_id: str, node_id: str
) -> Optional[dict[str, Any]]:
    """The enriched concept fields for a node, or `None` when not yet enriched."""
    path = concepts_path(workstreams_dir, workstream_id, node_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_concepts(
    workstreams_dir: Path,
    workstream_id: str,
    node_id: str,
    fields: dict[str, Any],
) -> None:
    """Persist a node's concept fields. UTF-8 always (clause text carries
    Unicode — §, en-dashes — that the Windows platform default cannot write).
    """
    path = concepts_path(workstreams_dir, workstream_id, node_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {field: fields.get(field) for field in CONCEPT_FIELDS}
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def validate_metadata(body: Any) -> Optional[tuple[int, str, str, Optional[str]]]:
    """`None` when the body is a saveable profile, else the first rule it breaks
    as `(status, code, message, field)`.

    Returns the first problem rather than a list: the form rings one input at a
    time, and a drafter fixing a typo'd key does not need to hear about the rest.

    Nothing here is sanitised or coerced — every value is rendered as text by the
    panel, never as markup, so unlike a draft there is no injection surface to
    close. What this does refuse is a payload that would quietly lose an edit: an
    unknown key (a typo the drafter would never see corrected), a wrong type, and
    `task_type`, which belongs to the node and is set once at creation.
    """
    if not isinstance(body, dict):
        return (400, "INVALID_METADATA", "Metadata must be an object.", None)

    # Ahead of the unknown-key check: `task_type` is not a metadata field, but
    # calling it unknown would be misleading — it exists, it is just permanent.
    if "task_type" in body:
        return (
            400,
            "TASK_TYPE_IMMUTABLE",
            "A deliverable kind is set when the document is created and cannot be changed.",
            "task_type",
        )

    for key, value in body.items():
        if key not in CONCEPT_FIELDS:
            return (
                400,
                "UNKNOWN_METADATA_FIELD",
                f"{key!r} is not a metadata field.",
                key,
            )
        problem = _validate_field(key, value)
        if problem is not None:
            return problem
    return None


def _validate_field(
    field: str, value: Any
) -> Optional[tuple[int, str, str, Optional[str]]]:
    """Type then size, for one field. Type first: a size check on a value of the
    wrong type would report the wrong problem, or crash on `len()`."""
    if value is None:
        return None

    if field in LIST_FIELDS:
        if isinstance(value, str):
            return _too_long(field, value, MAX_FIELD_CHARS)
        if not isinstance(value, list):
            return (
                400,
                "INVALID_METADATA",
                f"{field} must be a list of strings, a string, or null.",
                field,
            )
        if not all(isinstance(member, str) for member in value):
            return (
                400,
                "INVALID_METADATA",
                f"Every {field} value must be a string.",
                field,
            )
        if len(value) > MAX_LIST_MEMBERS:
            return (
                413,
                "METADATA_TOO_LARGE",
                f"{field} holds at most {MAX_LIST_MEMBERS} values.",
                field,
            )
        for member in value:
            problem = _too_long(field, member, MAX_LIST_MEMBER_CHARS)
            if problem is not None:
                return problem
        return None

    if not isinstance(value, str):
        return (400, "INVALID_METADATA", f"{field} must be a string or null.", field)
    return _too_long(field, value, MAX_FIELD_CHARS)


def _too_long(
    field: str, value: str, limit: int
) -> Optional[tuple[int, str, str, Optional[str]]]:
    if len(value) > limit:
        return (
            413,
            "METADATA_TOO_LARGE",
            f"{field} exceeds {limit} characters.",
            field,
        )
    return None


def normalise_metadata(body: dict[str, Any]) -> dict[str, Any]:
    """Trim, and collapse every shade of blank to `None`.

    "Cleared" and "never set" must be one state on disk, because the panel reads
    a `null` as "not set yet" and there is no third state a drafter can express.
    So `"  "`, `""`, `[]`, and a list whose members were all whitespace all land
    as `None` — a drafter who clears a field sees it read "Not set" on her next
    visit, exactly as if she had never touched it.

    Missing keys are left missing: `save_concepts` already normalises to the full
    nine-key set, and adding them here would duplicate that.
    """
    cleaned: dict[str, Any] = {}
    for key, value in body.items():
        if isinstance(value, str):
            cleaned[key] = value.strip() or None
        elif isinstance(value, list):
            members = [
                member.strip()
                for member in value
                if isinstance(member, str) and member.strip()
            ]
            cleaned[key] = members or None
        else:
            cleaned[key] = value
    return cleaned
