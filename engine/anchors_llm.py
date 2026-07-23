"""LLM-boundary segmenter — the non-BNM lane.

The model emits ONLY boundaries + labels ({anchor_label, starts_with, parent});
deterministic code locates each starts_with in the source, slices the verbatim
text between consecutive anchors, and verify_substring gates it. The model never
produces citation text. Reuses engine.clauses._find_anchor_positions (which
matches whitespace-insensitively but slices from the raw source, so text stays
byte-for-byte verbatim).

The model call is behind the injectable boundary_fn seam; tests inject a stub so
no network/credentials are needed (mirrors engine.connections finder_fn).
"""
from __future__ import annotations

import re
from typing import Callable, Optional

from engine.anchors import Anchor, verify_substring
from engine.clauses import _find_anchor_positions
from engine.config import FINDER_CRITIC_DEPLOYMENT
from engine.llm import call_chat, parse_json_response

# (document_id, source_markdown, doc_class) -> [{anchor_label, starts_with, parent}]
BoundaryFn = Callable[[str, str, str], list[dict]]

BOUNDARY_SYSTEM_PROMPT = (
    "You segment a legal/regulatory document into its structural units. "
    "Return a JSON array; each element is "
    '{"anchor_label": <the unit locator EXACTLY as printed, e.g. "Article 12(3)" '
    'or "Principle 4">, "starts_with": <the first few words of the unit\'s BODY '
    "text, copied verbatim, NO label prefix>, \"parent\": <the parent locator or "
    "null>}. "
    "Copy anchor_label verbatim from the heading — never invent or renumber. "
    "starts_with must be a verbatim quote of the body so it can be located in the "
    "source. Do not include preamble, page numbers, or dates as units."
)


def _default_boundary_fn(
    document_id: str, source_markdown: str, doc_class: str
) -> list[dict]:
    user = (
        f"doc_class: {doc_class}\ndocument_id: {document_id}\n\n"
        f"Document markdown:\n{source_markdown}"
    )
    raw = call_chat(FINDER_CRITIC_DEPLOYMENT, BOUNDARY_SYSTEM_PROMPT, user,
                    max_tokens=16384)
    data = parse_json_response(raw)
    if not isinstance(data, list):
        raise ValueError("boundary model did not return a JSON array")
    return data


_STRUCTURAL_MARKER_RE = re.compile(r"^(CHAPTER|SECTION|TITLE|ANNEX|Article|PART)\b")
_DIVIDER_LINE_RE = re.compile(r"^[ \t]*#*[ \t]*(CHAPTER|SECTION|TITLE|PART|ANNEX)\b")


def _trim_next_unit_heading(
    segment: str, next_label: Optional[str], next_snippet: Optional[str]
) -> str:
    """Trim the next unit's heading + any body that follows it off `segment`.

    `segment` is ``source_markdown[start:next_start]`` — this unit's body PLUS the
    next unit's scaffolding (its heading line, optionally preceded by a CHAPTER/
    SECTION/TITLE/PART/ANNEX divider) PLUS the first line(s) of the next unit's
    body (up to where its `starts_with` matched). The next unit's heading line
    contains `next_label`, so we cut the segment at the EARLIEST heading/divider
    that begins the next unit's scaffolding block — NOT by trimming trailing
    blocks (the scaffolding sits MID-gap, not at the tail).

    Strategy:
    1. If `next_label` is provided, find the earliest line that is a heading for
       `next_label` (``^\\s*#*\\s*<label>\\b``) and cut the segment at its start.
    2. Walk backwards over any structural divider blocks (CHAPTER/SECTION/TITLE/
       PART/ANNEX) that immediately precede that heading — separated only by blank
       lines — and cut before them too, so a "CHAPTER II\\n\\n## Article 2" gap is
       removed whole, not just the Article line.
    3. If `next_label` is absent (defensive fallback), trim a trailing block that
       starts with '#' or a structural marker.
    The result is always ``.rstrip()``-ed. If the cut would empty a non-empty
    body (heading at position 0 — shouldn't happen since body precedes it), the
    rstripped original is returned unchanged as a safety net.
    """
    if next_label:
        cut = len(segment)
        heading_re = re.compile(r"(?m)^[ \t]*#*[ \t]*" + re.escape(next_label) + r"\b")
        m = heading_re.search(segment)
        if m is not None:
            cut = m.start()
            # Absorb any structural divider block(s) immediately preceding the
            # next-label heading, separated only by blank lines.
            cut = _absorb_preceding_dividers(segment, cut)
        result = segment[:cut].rstrip()
        if not result and segment.strip():
            return segment.rstrip()
        return result

    # Defensive fallback: no next_label — trim a single trailing scaffolding block.
    stripped = segment.rstrip()
    sep = stripped.rfind("\n\n")
    if sep == -1:
        return stripped
    tail = stripped[sep + 2:].strip()
    if tail.startswith("#") or _STRUCTURAL_MARKER_RE.match(tail):
        return stripped[:sep].rstrip()
    return stripped


def _absorb_preceding_dividers(segment: str, cut: int) -> int:
    """Move `cut` earlier over blank-line-separated structural divider blocks.

    Given a cut point at the start of the next unit's heading, walk backwards over
    any immediately-preceding blocks (separated only by blank lines) whose first
    line is a CHAPTER/SECTION/TITLE/PART/ANNEX divider, returning the new (earlier)
    cut point so those dividers are also removed.
    """
    while True:
        prefix = segment[:cut]
        # Strip trailing blank lines between the divider block and the heading.
        stripped_prefix = prefix.rstrip("\n")
        trailing_ws = len(prefix) - len(stripped_prefix)
        if trailing_ws == 0:
            # No blank-line separation; heading directly abuts prior content.
            return cut
        block_start = stripped_prefix.rfind("\n\n")
        block = (
            stripped_prefix[block_start + 2:]
            if block_start != -1
            else stripped_prefix
        )
        first_line = block.split("\n", 1)[0]
        if not _DIVIDER_LINE_RE.match(first_line):
            return cut
        cut = block_start + 2 if block_start != -1 else 0


def _drop(report: Optional[list[dict]], document_id: str, unit: dict,
          reason: str) -> None:
    if report is None:
        return
    report.append({
        "document_id": document_id,
        "anchor_label": unit.get("anchor_label"),
        "reason": reason,
        "starts_with": unit.get("starts_with"),
    })


def llm_boundary_segment(
    document_id: str,
    source_markdown: str,
    *,
    doc_class: str,
    shortname: str,
    boundary_fn: Optional[BoundaryFn] = None,
    dropped_report: Optional[list[dict]] = None,
) -> list[Anchor]:
    """Segment via model-emitted boundaries + deterministic verbatim slicing.

    anchor_id is "{shortname} {anchor_label}" (e.g. "EU AI Act Article 12(3)").
    A unit whose starts_with is empty, not found, or ambiguous is dropped (into
    dropped_report if supplied), never emitted. Every returned anchor is
    re-checked with verify_substring.
    """
    fn = boundary_fn if boundary_fn is not None else _default_boundary_fn
    units = fn(document_id, source_markdown, doc_class)

    # Resolve each unit to a start offset first, so we can slice between anchors.
    resolved: list[tuple[dict, int]] = []
    for unit in units:
        snippet = (unit.get("starts_with") or "").strip()
        if not snippet:
            _drop(dropped_report, document_id, unit, "empty_starts_with")
            continue
        positions = _find_anchor_positions(source_markdown, snippet)
        if not positions:
            _drop(dropped_report, document_id, unit, "not_found")
            continue
        if len(positions) > 1:
            _drop(dropped_report, document_id, unit, "ambiguous")
            continue
        resolved.append((unit, positions[0]))

    resolved.sort(key=lambda pair: pair[1])
    anchors: list[Anchor] = []
    for i, (unit, start) in enumerate(resolved):
        if i + 1 < len(resolved):
            next_unit, next_start = resolved[i + 1]
            # The gap between this body-start and the next body-start ends with the
            # next unit's heading/label; trim it so the citation stops at this
            # unit's own content (CLAUDE.md verbatim-clause rule).
            text = _trim_next_unit_heading(
                source_markdown[start:next_start],
                next_unit.get("anchor_label"),
                (next_unit.get("starts_with") or "").strip() or None,
            )
        else:
            # Last unit: no next heading to trim, slice to end of source.
            text = source_markdown[start:len(source_markdown)].strip()
        if not text:
            _drop(dropped_report, document_id, unit, "empty_text")
            continue
        label = unit["anchor_label"]
        parent = unit.get("parent")
        anchor: Anchor = {
            "anchor_id": f"{shortname} {label}",
            "anchor_label": label,
            "text": text,
            "doc_class": doc_class,
            "document_id": document_id,
            "heading_path": [],
            "page_span": None,
            "parent_anchor": f"{shortname} {parent}" if parent else None,
        }
        verify_substring(anchor, source_markdown)  # defensive re-check
        anchors.append(anchor)
    return anchors
