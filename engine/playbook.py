"""Per-stage instructions the drafter gives the Copilot.

    data/workstreams/{workstream_id}/playbook.json
        {"brainstorm": "...", "draft": "...", "write": "...", "deliver": "...",
         "updated_at": "2026-08-02T10:22:14Z"}

One per workstream, so conventions recorded while drafting one document reach
every other draft beside it. Free text in the drafter's own words — nothing here
is parsed, validated against a schema, or interpreted structurally. It is prompt
input, injected at the stage it belongs to.

**`/explore-task` has no field, deliberately.** The Copilot's first stage exists
to reveal what a document's regulatory profile actually records. A
drafter-authored override there would let the tool report a regulatory identity
the document does not have — the opposite of what the stage is for. Storing an
editable section for it would be the first step towards that, so the key does not
exist at all: a client that sends one has it ignored, the same way
`_parse_copilot_request` ignores a stale `intent`.

**Every section starts empty.** Unlike `engine.guardrails`, there are no shipped
defaults: the Copilot's current behaviour is the baseline, and there is no body of
evidence saying what a good default instruction would be. Pre-filled text a
drafter did not write would be followed silently, which is worse than an empty
box.

**Absence writes nothing.** A workstream that has never saved a playbook returns
four empty strings; no file is created on read. That is what keeps the three
retired fixtures byte-identical on disk (see the retired-fixtures rule in
`CLAUDE.md`).
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# The four editable stages, in the order the Copilot runs them. Mirrors
# `SLASH_COMMANDS` in `frontend/src/features/drafting-workspace/copilotV2Data.ts`
# minus `/explore-task`, which is locked — see the module docstring.
SECTIONS: tuple[str, ...] = ("brainstorm", "draft", "write", "deliver")

# The stage id a request names, mapped to its stored section. `/explore-task` is
# absent on purpose: naming it is not an error, it simply selects nothing.
STAGE_TO_SECTION: dict[str, str] = {
    "/brainstorm": "brainstorm",
    "/draft": "draft",
    "/write": "write",
    "/deliver": "deliver",
    # Tolerate the bare forms too — a client that sends "write" rather than
    # "/write" means the same thing, and refusing it would be pedantry.
    "brainstorm": "brainstorm",
    "draft": "draft",
    "write": "write",
    "deliver": "deliver",
}

# 20 000 characters per section. A backstop against a paste accident, not a limit
# a drafter writing conventions in prose can reach.
MAX_SECTION_CHARS: int = 20_000


class PlaybookValidationError(Exception):
    """A save was refused. Carries a stable `code`, a message, and the offending
    `field` so the form can ring the right textarea instead of showing a banner."""

    def __init__(self, status: int, code: str, message: str, field: Optional[str]) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.field = field


def playbook_path(workstreams_dir: Path, workstream_id: str) -> Path:
    return workstreams_dir / workstream_id / "playbook.json"


def empty() -> dict[str, Any]:
    """What a workstream that has never saved one looks like."""
    return {
        **{section: "" for section in SECTIONS},
        "updated_at": None,
        "is_default": True,
    }


def load(workstreams_dir: Path, workstream_id: str) -> dict[str, Any]:
    """A workstream's playbook, or four empty sections. Never writes.

    `is_default` tells the interface whether it is looking at an untouched
    workstream or something the drafter saved — which is not the same as checking
    whether the sections are blank, because clearing every section is a legitimate
    save.
    """
    path = playbook_path(workstreams_dir, workstream_id)
    if not path.exists():
        return empty()
    record = json.loads(path.read_text(encoding="utf-8"))
    return {
        **{section: record.get(section, "") or "" for section in SECTIONS},
        "updated_at": record.get("updated_at"),
        "is_default": False,
    }


def validate(body: Any) -> None:
    """Raise `PlaybookValidationError` unless `body` is a saveable playbook.

    Unknown keys — including `explore_task` — are IGNORED rather than rejected. A
    stale client should not get a 400 for sending a field the server no longer
    wants, which is the same courtesy `_parse_copilot_request` extends to a
    leftover `intent`.
    """
    if not isinstance(body, dict):
        raise PlaybookValidationError(
            400, "INVALID_PLAYBOOK", "A playbook must be an object.", None
        )
    for section in SECTIONS:
        if section not in body:
            continue
        value = body[section]
        if not isinstance(value, str):
            raise PlaybookValidationError(
                400, "INVALID_PLAYBOOK", f"{section} must be a string.", section
            )
        if len(value) > MAX_SECTION_CHARS:
            raise PlaybookValidationError(
                413,
                "PLAYBOOK_TOO_LARGE",
                f"{section} holds at most {MAX_SECTION_CHARS} characters.",
                section,
            )


def save(
    workstreams_dir: Path,
    workstream_id: str,
    body: dict[str, Any],
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Persist a playbook as a FULL REPLACEMENT of the four sections.

    The form always sends all four, so a section the client omits lands as `""` —
    which makes a save exactly what the drafter saw on screen, with no stale
    instruction surviving underneath. Same discipline as the metadata route.

    UTF-8 always: a convention quotes clause text, which carries § and en-dashes
    that the cp1252 platform default mangles on Windows.
    """
    validate(body)
    stamp = (now or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z")
    record = {
        **{section: body.get(section) or "" for section in SECTIONS},
        "updated_at": stamp,
    }
    path = playbook_path(workstreams_dir, workstream_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return {**record, "is_default": False}


def section_for_stage(
    workstreams_dir: Path, workstream_id: str, stage: Optional[str]
) -> str:
    """The instruction text for the running stage, or `""`.

    Returns `""` for an absent stage, for `/explore-task`, for an unrecognised
    stage, and for a stage whose section the drafter left empty. The caller adds
    no PLAYBOOK block at all in that case — so a workstream with no playbook
    produces a prompt byte-identical to the one it produced before this feature
    existed.

    Only ONE section is ever returned. That is what stops `/deliver`'s approval
    layers leaking into `/draft`'s structure.
    """
    if not stage:
        return ""
    section = STAGE_TO_SECTION.get(stage.strip())
    if section is None:
        return ""
    return load(workstreams_dir, workstream_id)[section]
