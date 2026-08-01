"""Per-node regulatory profile — the seven-field metadata the panel calls Metadata.

    data/workstreams/{workstream_id}/metadata/{node_id}.json     (canonical)
    data/workstreams/{workstream_id}/concepts/{node_id}.json     (legacy, read-only)

**Two directories, and the older name is a trap.** This store was called
`concepts/` before the word was repurposed. When axis extraction landed,
`concepts` became the name for a document's **extracted axes** — served from
`axes/` and surfaced as the node-detail response's `concepts` block (see
`engine.api._node_concepts_block`). Those axes are the real concepts. Meanwhile
the API and the interface have always called *this* seven-field profile
`metadata`: the write route is `PUT .../nodes/{id}/metadata` and the response key
is `metadata`. So the directory named `concepts/` was the one thing in the system
that was not concepts, and a reader who opened it looking for axes read the wrong
file. Renamed on 1 Aug 2026 to close that.

`load_metadata` reads `metadata/` first and falls back to `concepts/`.
**The fallback is permanent, not transitional — do not remove it.** Exactly three
workstreams depend on it: the retired fixtures `opres-v2`, `rmit-v2-2025` and
`open-finance-ed`, whose contents are recorded history rather than a defect to
correct (see the retired-fixtures rule in `CLAUDE.md`) and which the engine suite
reads by id. The live demo workstream `open-finance-pd-2026` was migrated
outright — that rule only ever covered retired fixtures — so it reads
canonically and is not a fallback consumer. `save_metadata` always writes
`metadata/`, so a retired fixture saved through the app moves forward one node at
a time, and `metadata/` wins from then on.

Absence is the common, expected case — most nodes have not been enriched, and
that is not an error. `load_metadata` returns `None` in that case, and the
caller falls back to the placeholder exactly like an unanalysed edge falls
back to "not analysed" rather than erroring (`findings.FindingsNotAnalysedError`).

Every field here is either a value already carried structurally on the node
(`owner`) or a structured reference already documented in the corpus — never
invented. A field the enrichment script could not honestly derive is `null`,
not guessed.
"""

import json
from pathlib import Path
from typing import Any, Optional

# The seven regulatory-profile fields, in the order the panel renders them.
#
# Honesty rules (unchanged): every populated value is either a value already
# carried structurally on the node (`policy_owner`, `issuance_date`), or a
# structured reference already documented elsewhere in the corpus
# (`legal_provision` — the same kind of value `pursuant_to` already holds on a
# node). A field that cannot be honestly derived is `null`, not guessed.
# `ismp_classification` in particular has NO offline source (its authority is
# CAS's RH publication form, which the repo does not hold) and is therefore
# `null` everywhere today — the field exists so the UI can render "pending"
# rather than hide the concept.
#
# History, so a reader is not surprised by what side-files on disk contain:
# `keywords` was removed on 30 Jul 2026 (the extracted axes cover a document's
# topics from the document itself) and `empowerment_framework` on 31 Jul 2026
# (`legal_provision` plus the node's `pursuant_to` already carry the statutory
# basis). On 1 Aug 2026 `legal_basis` was renamed `legal_provision`, and
# `requirement` returned as `policy_requirement` — this time earning its row,
# because it is the axis list the Recommendations feature reasons over rather
# than a restatement of the draft.
#
# Retired workstreams were deliberately NOT migrated, so `opres-v2`,
# `rmit-v2-2025` and `open-finance-ed` still hold `legal_basis` on disk. Nothing
# breaks: `load_metadata` returns the raw dict and the node-detail route spreads
# it, so the legacy key still reaches the client — it simply no longer lands in
# a panel row. The next save through the API rewrites the file to exactly this
# tuple.
METADATA_FIELDS: tuple[str, ...] = (
    "policy_owner",
    "applicability",
    "legal_provision",
    "issuance_date",
    "effective_date",
    "policy_requirement",
    "ismp_classification",
)


# The list-valued fields: each holds several values, entered as one
# comma-separated line and rendered as chips. Every one tolerates a bare string
# too, because side-files written before the field became a list carry
# scalars — including the three retired workstreams, whose `applicability` is
# still a sentence.
LIST_FIELDS: frozenset[str] = frozenset(
    {"applicability", "legal_provision", "policy_requirement"}
)

# The four BNM security classifications, in ascending sensitivity. A drafter
# picks one or leaves it unset — unset renders as pending rather than as a
# guess, because misclassifying a document has real handling consequences.
ISMP_CLASSIFICATIONS: tuple[str, ...] = ("UMUM", "TERHAD", "SULIT", "RAHSIA")

# 2000 characters per SCALAR field. The remaining scalars are a name, two dates
# and a classification code, so this is a backstop against a paste accident
# rather than a limit a drafter can reach. The list fields are bounded by
# MAX_LIST_MEMBERS instead — see below on why their members are uncapped.
MAX_FIELD_CHARS: int = 2000

# A profile lists Acts and obligations, not a corpus: 50 chips is far past what a
# drafter would type, and past it the panel would be unreadable anyway. This
# bounds the number of values, not their length — members are deliberately
# uncapped, because a statutory citation runs long ("Financial Services Act 2013,
# section 143(2), read together with…") and so does a policy requirement, and
# truncating either would corrupt it rather than tidy it.
MAX_LIST_MEMBERS: int = 50


def metadata_path(workstreams_dir: Path, workstream_id: str, node_id: str) -> Path:
    """The canonical location of a node's profile. Every write goes here."""
    return workstreams_dir / workstream_id / "metadata" / f"{node_id}.json"


def legacy_metadata_path(
    workstreams_dir: Path, workstream_id: str, node_id: str
) -> Path:
    """The pre-1-Aug-2026 location, read-only.

    **This is permanent. Do not delete it, and do not migrate the files it
    points at.** The three retired fixtures (`opres-v2`, `rmit-v2-2025`,
    `open-finance-ed`) hold their profiles here and are never to be rewritten — a
    retired fixture's contents are recorded history, and the engine suite reads
    several of them by id, so "tidying" this away silently changes what those
    tests assert.

    The live demo workstream `open-finance-pd-2026` is NOT a consumer: it was
    migrated to `metadata/` outright, because the no-migration rule only ever
    covered retired fixtures. So this path serves retired fixtures alone.

    Nothing writes here. `save_metadata` always targets `metadata_path`, so a
    node saved through the app moves forward permanently.
    """
    return workstreams_dir / workstream_id / "concepts" / f"{node_id}.json"


def load_metadata(
    workstreams_dir: Path, workstream_id: str, node_id: str
) -> Optional[dict[str, Any]]:
    """A node's regulatory profile, or `None` when it has none.

    Reads `metadata/` first, then falls back to the legacy `concepts/` path (see
    `legacy_metadata_path` for why that fallback is permanent). When both exist
    `metadata/` wins, because it is the only one anything writes — so the newer
    value is always the one served.
    """
    for path in (
        metadata_path(workstreams_dir, workstream_id, node_id),
        legacy_metadata_path(workstreams_dir, workstream_id, node_id),
    ):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def save_metadata(
    workstreams_dir: Path,
    workstream_id: str,
    node_id: str,
    fields: dict[str, Any],
) -> None:
    """Persist a node's profile to `metadata/`, never to the legacy path.

    UTF-8 always (clause text carries Unicode — §, en-dashes — that the Windows
    platform default cannot write). A legacy `concepts/` file for the same node
    is left exactly as it is; `load_metadata` will simply stop reaching it.
    """
    path = metadata_path(workstreams_dir, workstream_id, node_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {field: fields.get(field) for field in METADATA_FIELDS}
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
        if key not in METADATA_FIELDS:
            return (
                400,
                "UNKNOWN_METADATA_FIELD",
                f"{key!r} is not a metadata field.",
                key,
            )
        problem = _validate_field(key, value)
        if problem is not None:
            return problem

    # A closed vocabulary, checked after the type rules so a non-string reports as
    # a type error rather than a bad classification. `None` stays legal — unset is
    # the honest state for a document whose classification nobody has recorded.
    ismp = body.get("ismp_classification")
    if ismp is not None and ismp not in ISMP_CLASSIFICATIONS:
        return (
            400,
            "INVALID_ISMP_CLASSIFICATION",
            f"ismp_classification must be one of {list(ISMP_CLASSIFICATIONS)}, "
            f"got {ismp!r}",
            "ismp_classification",
        )
    return None


def _validate_field(
    field: str, value: Any
) -> Optional[tuple[int, str, str, Optional[str]]]:
    """Type then size, for one field. Type first: a size check on a value of the
    wrong type would report the wrong problem, or crash on `len()`."""
    if value is None:
        return None

    # A list field carries statutory citations, which are uncapped in length —
    # both as a bare string and per member. See MAX_LIST_MEMBERS on why only the
    # count is bounded.
    if field in LIST_FIELDS:
        if isinstance(value, str):
            return None
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

    Missing keys are left missing: `save_metadata` already normalises to the full
    `METADATA_FIELDS` set, and adding them here would duplicate that.
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
