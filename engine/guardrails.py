"""The rules the recommendations engine follows, authored by the drafter.

    data/workstreams/{workstream_id}/guardrails.json
        {"body": "...", "updated_at": "2026-08-02T09:02:11Z"}

One per workstream, so a rule learned drafting one document protects every other
draft beside it. Free text in the drafter's own words — nothing here is parsed,
validated against a schema, or interpreted structurally. It is prompt input.

**Absence serves DEFAULT_GUARDRAILS and writes nothing.** A workstream that has
never been edited is not an error and does not need a file created on read: the
five defaults below are the shipped content, so the box is populated and useful
from the first day. That also keeps the three retired fixtures byte-identical on
disk (see the retired-fixtures rule in `CLAUDE.md`) — reading a retired
workstream's guardrails must not create a file inside it.

**Only the drafter writes here.** No generation, comment, or rewrite ever edits
this file. That is deliberate: the alternative — the tool re-interpreting a
drafter's comment into a standing rule — has the model authoring the rules it
then follows, and an over-broad rule would silently suppress good
recommendations until someone thought to read the box. A rule that governs every
future generation is worth one deliberate action.

An empty body is a valid, deliberate state, not a signal to reinstate the
defaults. A drafter who clears the box means it; the interface says plainly what
that implies rather than quietly overruling her.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# 20 000 characters. A backstop against a paste accident, not a limit a drafter
# writing rules in prose can reach — the five defaults together run under 2 000.
MAX_GUARDRAILS_CHARS: int = 20_000


# The five defaults, in plain language, derived from a real BNM policy officer's
# assessment of nine AI-generated recommendations against the Open Finance
# Exposure Draft (see docs/specs/workstream-brain/recommendations/spec.md,
# Appendix A). Each of the first four is one specific, repeatable way that
# sample failed; the fifth is the repo's standing verbatim-citation rule.
#
# These are a starting point, not a floor: every one of them is editable and
# deletable. A rule the drafter cannot change is not accountable to her, which is
# the problem this file exists to fix. What she cannot switch off is the citation
# guarantee itself — that is enforced in code (the evidence floor in
# `engine.recommendations`), not by this text.
DEFAULT_GUARDRAILS: str = """\
1. House convention — cross-references stay general.
   Never recommend that a policy document cite another policy document by
   specific provision number. BNM policy documents cross-reference each other in
   general terms deliberately: provision numbering shifts when a document is
   reissued, and a pinned reference silently goes stale. Recommending a mapping
   annex to specific numbered provisions works against that on purpose.

2. Scope boundary — stay inside what the draft covers.
   Recommend only within the applicability the draft itself states. Do not
   propose obligations on classes of entity the instrument does not cover. An
   asymmetry between covered and uncovered entities is not a gap if the
   uncovered entities are outside scope by design.

3. Terminology false-friend — check the term means the same thing.
   Before asserting a difference against a peer regulator, establish that a
   shared term denotes the same thing on both sides. Where it cannot be
   established from the documents themselves, say so instead of asserting the
   difference. A shared acronym is not evidence of a shared concept.

4. Alignment from silence — mutual vagueness is not agreement.
   Where two documents are both silent or both high-level on a point, report
   that neither elaborates. Do not describe it as alignment: that overstates how
   closely the draft tracks an international standard, and a reader would infer
   a benchmark that was never set.

5. Evidence floor — quote the clause or do not make the claim.
   Every recommendation rests on at least one accepted finding, named, with its
   clause number and clause text reproduced word-for-word. Write nothing the
   accepted evidence does not support. Where no accepted finding bears on a
   point, say so rather than filling the gap.
"""


class GuardrailsTooLargeError(Exception):
    """The body exceeds MAX_GUARDRAILS_CHARS. Carries the offending length."""

    def __init__(self, length: int) -> None:
        super().__init__(f"Guardrails body is {length} characters")
        self.length = length


def guardrails_path(workstreams_dir: Path, workstream_id: str) -> Path:
    return workstreams_dir / workstream_id / "guardrails.json"


def load(workstreams_dir: Path, workstream_id: str) -> dict[str, Any]:
    """A workstream's guardrails, or the five defaults when it has none.

    Never writes. `is_default` tells the interface whether it is looking at
    shipped content or something the drafter saved — which is not the same as
    comparing the text, because a drafter may legitimately save a body that
    happens to match the defaults.
    """
    path = guardrails_path(workstreams_dir, workstream_id)
    if not path.exists():
        return {
            "body": DEFAULT_GUARDRAILS,
            "updated_at": None,
            "is_default": True,
        }
    record = json.loads(path.read_text(encoding="utf-8"))
    return {
        "body": record.get("body", ""),
        "updated_at": record.get("updated_at"),
        "is_default": False,
    }


def save(
    workstreams_dir: Path,
    workstream_id: str,
    body: str,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Persist a workstream's guardrails. Returns the stored record.

    An empty body is accepted — clearing the box is a deliberate act, and the
    tool reports what it means rather than reinstating the defaults behind the
    drafter's back.

    UTF-8 always: a rule quotes clause text, which carries § and en-dashes that
    the cp1252 platform default mangles on Windows (see
    docs/learnings/pattern-engine-artifact-writes-utf8.md).
    """
    if len(body) > MAX_GUARDRAILS_CHARS:
        raise GuardrailsTooLargeError(len(body))

    stamp = (now or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z")
    record = {"body": body, "updated_at": stamp}
    path = guardrails_path(workstreams_dir, workstream_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return {**record, "is_default": False}


def body_for_prompt(workstreams_dir: Path, workstream_id: str) -> str:
    """The guardrails text the generation and rewrite prompts are built from.

    Reads whatever stands right now, so an edit takes effect on the very next
    generation without anything being invalidated or rebuilt. Returns `""` when
    the drafter has deliberately emptied the box — the caller omits the
    guardrails block entirely rather than falling back to the defaults she just
    deleted.
    """
    return load(workstreams_dir, workstream_id)["body"]
