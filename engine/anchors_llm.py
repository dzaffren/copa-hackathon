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


def _trim_next_unit_heading(
    segment: str, next_label: Optional[str], next_snippet: Optional[str]
) -> str:
    """Trim the next unit's heading/label block off the tail of `segment`.

    `segment` is ``source_markdown[start:next_start]`` — this unit's body PLUS the
    next unit's leading scaffolding (its heading/label line(s) that sit in the gap
    between this unit's body and the next unit's body, `next_start`). Because the
    boundary model quotes `starts_with` from the *body* (no label prefix), a raw
    slice up to the next body picks up that scaffolding. This returns the segment
    with the trailing heading block removed.

    Rule (deliberately simple, mirrors clauses._trim_trailing_label's intent for a
    markdown-heading world): headings are blank-line separated, so the trailing
    scaffolding is the block after the LAST ``"\\n\\n"``. Cut there IFF that final
    block looks like the next unit's heading — it starts with a markdown ``#``
    marker, or it contains the next unit's `anchor_label`/`starts_with`. If the
    final block does NOT look like a heading, it is genuine body content and is
    left intact (never cut into the current unit's body). The result is stripped of
    trailing whitespace either way.
    """
    stripped = segment.rstrip()
    sep = stripped.rfind("\n\n")
    if sep == -1:
        return stripped
    tail = stripped[sep + 2:].strip()
    if not tail:
        return stripped
    looks_like_heading = tail.startswith("#")
    if not looks_like_heading and next_label:
        looks_like_heading = next_label.strip() in tail
    if not looks_like_heading and next_snippet:
        looks_like_heading = next_snippet.strip() in tail
    if not looks_like_heading:
        return stripped
    return stripped[:sep].rstrip()


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
