"""Working-draft persistence for the drafting workspace.

    data/workstreams/{workstream_id}/drafts/{node_id}.json
        {"node_id", "content_html", "last_saved_at"}

The draft is the one document in a workstream that is *written*, not merely read
— every other node is published context. It arrives from a `contentEditable`
surface, which means it arrives as attacker-shaped HTML: the browser will happily
hand us a pasted `<script>`, an `onerror=` attribute, or a `javascript:` href.
The frontend sanitizes with DOMPurify before the PUT, but that is a nicety, not a
control — anyone can curl this endpoint. `sanitize()` below is the real boundary
and runs on every write regardless of what the client claims to have done.

All writes are UTF-8: the corpus carries § and en-dashes, which the cp1252
platform default mangles on Windows (see
docs/learnings/pattern-engine-artifact-writes-utf8.md).
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import bleach

# Structural tags a policy draft needs, and nothing else. No <a> (no link
# targets to smuggle javascript: through), no <img> (no onerror), no <style>.
# `span`/`div` survive because the Copilot snippet wraps in them.
ALLOWED_TAGS: frozenset[str] = frozenset(
    {"h1", "h2", "h3", "p", "strong", "em", "u", "ul", "ol", "li", "div", "span", "br"}
)

# `class` only, and only on the wrappers that carry it. This is what lets an
# inserted Copilot snippet keep its `copilot-snippet` marker — the visual
# provenance signal that tells a drafter which text they did not write — while
# still dropping every event handler, since `on*` is simply not on the list.
ALLOWED_ATTRS: dict[str, list[str]] = {"div": ["class"], "span": ["class"], "p": ["class"]}

# 200 KB after sanitization. A policy document is text; anything past this is
# either a paste accident or someone probing.
MAX_DRAFT_BYTES: int = 200 * 1024


# Elements whose *content* is not prose and must go with the tag.
#
# This exists because of a real bleach behaviour: `strip=True` removes a
# disallowed tag but KEEPS its text, which is right for `<font>Hello</font>`
# (→ `Hello`) and wrong for `<script>alert(1)</script>` (→ `alert(1)`, sitting
# in the policy document as visible text). Neutralised, never executable — but
# a draft is not the place for orphaned JavaScript source.
_CONTENT_BEARING = "script|style|iframe|object|embed|template|noscript"
_DROP_WHOLE_ELEMENT = re.compile(
    rf"<\s*({_CONTENT_BEARING})\b[^>]*>.*?<\s*/\s*\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
# An unclosed `<script>` never gets matched by the pair above; drop from the
# opening tag to the end rather than let its body through as text.
_DROP_DANGLING_OPEN = re.compile(
    rf"<\s*({_CONTENT_BEARING})\b[^>]*>.*\Z", re.IGNORECASE | re.DOTALL
)


class DraftTooLargeError(Exception):
    """Sanitized `content_html` exceeds MAX_DRAFT_BYTES."""


class DraftEmptyError(Exception):
    """Sanitization consumed the whole payload — nothing survived to save."""


def sanitize(content_html: str) -> str:
    """Strip everything but the allowlisted structural tags.

    Two passes, and the order is the point. The regex pass drops script-like
    elements *with their bodies*; it is a tidiness measure, not the control, and
    is allowed to be imperfect — anything it misses still meets bleach, which
    strips the tag so nothing can execute either way. bleach is the boundary.

    `strip=True` drops disallowed tags while keeping their text, so a paste from
    Word loses its chrome but keeps its words. `strip_comments=True` because a
    comment can hide a conditional-comment payload. The `javascript:` URL case
    needs no special handling: no URL-bearing attribute is allowlisted at all.
    """
    text = content_html or ""
    text = _DROP_WHOLE_ELEMENT.sub("", text)
    text = _DROP_DANGLING_OPEN.sub("", text)
    return bleach.clean(
        text,
        tags=set(ALLOWED_TAGS),
        attributes=ALLOWED_ATTRS,
        strip=True,
        strip_comments=True,
    )


def draft_path(workstreams_dir: Path, workstream_id: str, node_id: str) -> Path:
    return workstreams_dir / workstream_id / "drafts" / f"{node_id}.json"


def load(workstreams_dir: Path, workstream_id: str, node_id: str) -> dict[str, Any]:
    """The saved draft, or an empty one when the task has never been drafted.

    A missing file is not an error: a task node exists before its draft does, and
    the workspace should open on a blank page rather than a 404.
    """
    path = draft_path(workstreams_dir, workstream_id, node_id)
    if not path.exists():
        return {"node_id": node_id, "content_html": "", "last_saved_at": None}
    return json.loads(path.read_text(encoding="utf-8"))


def save(
    workstreams_dir: Path,
    workstream_id: str,
    node_id: str,
    content_html: str,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Sanitize, size-check, and persist a draft. Returns the saved record.

    Order matters: sanitize first, then measure. Measuring the raw payload would
    let a 300 KB blob of `<script>` 413 instead of being cleaned to nothing, and
    would reject a legitimate draft that only looked oversized because of markup
    we were about to strip anyway.
    """
    cleaned = sanitize(content_html)
    if len(cleaned.encode("utf-8")) > MAX_DRAFT_BYTES:
        raise DraftTooLargeError(len(cleaned))
    # Distinguish "you sent nothing" (fine — clearing a draft is legitimate)
    # from "you sent something and none of it survived" (the payload was
    # entirely markup we refuse, which is worth telling the caller about).
    if not cleaned.strip() and (content_html or "").strip():
        raise DraftEmptyError()

    stamp = (now or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z")
    record = {"node_id": node_id, "content_html": cleaned, "last_saved_at": stamp}
    path = draft_path(workstreams_dir, workstream_id, node_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return record
