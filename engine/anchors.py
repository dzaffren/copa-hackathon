"""Anchor data model + AnchorIndex — the doc-class-aware citation foundation
that supersedes engine/clauses.py::ClauseIndex.

Adopted from the anchor-segmentation design (docs/superpowers/specs/
2026-07-22-anchor-segmentation-design.md). Segmenter strategies register here
via SegmenterRegistry (Task 2+). Every anchor's `text` is a LITERAL substring of
the source markdown — the verbatim-citation guardrail, enforced by
verify_substring at build time.
"""
from __future__ import annotations

from typing import Optional, TypedDict

# The declared document classes a segmenter can be registered for.
DOC_CLASSES: tuple[str, ...] = (
    "structured-rules",  # BNM PDs — deterministic regex (engine.clauses)
    "legislative",       # EU AI Act, PDPA — Article N + (n) numbering
    "framework",         # NIST/OECD/Basel/MAS — numbered principles + prose
    "prose",             # declared escape hatch — verbatim chunks, no locator
)


class Anchor(TypedDict):
    """A verbatim, code-verified passage of source markdown, addressable by
    `anchor_id`. Optional fields are always present (empty list / None)."""

    anchor_id: str
    anchor_label: str
    text: str
    doc_class: str
    document_id: str
    heading_path: list[str]
    page_span: Optional[tuple[int, int]]
    parent_anchor: Optional[str]


class AnchorCitation(TypedDict):
    """The citation shape carried on Connection / UnsupportedConnection."""

    anchor_id: str
    anchor_label: str
    text: str
    doc_class: str


class AnchorTextNotFoundError(Exception):
    """Raised by verify_substring when an anchor's text is not a literal
    substring of its source markdown."""


def verify_substring(anchor: Anchor, source_markdown: str) -> None:
    """Raise AnchorTextNotFoundError if anchor['text'] is not a literal substring
    of source_markdown. The message names the anchor_id and previews the text."""
    text = anchor["text"]
    if text in source_markdown:
        return
    raise AnchorTextNotFoundError(
        f"Anchor {anchor['anchor_id']!r} text not found in source markdown "
        f"(first 80 chars: {text[:80]!r}; source was {len(source_markdown)} chars)."
    )


class AnchorIndex:
    """Read-only index of anchors keyed by anchor_id. Construction is strict:
    a duplicate anchor_id raises ValueError rather than silently overwriting."""

    def __init__(self, anchors: list[Anchor]) -> None:
        self._primary: dict[str, Anchor] = {}
        for anchor in anchors:
            aid = anchor["anchor_id"]
            if aid in self._primary:
                raise ValueError(f"Duplicate anchor_id {aid!r} in AnchorIndex")
            self._primary[aid] = anchor

    def get(self, anchor_id: str) -> Optional[Anchor]:
        return self._primary.get(anchor_id)

    def all(self) -> list[Anchor]:
        return list(self._primary.values())

    def by_document(self, document_id: str) -> list[Anchor]:
        return [a for a in self._primary.values() if a["document_id"] == document_id]

    def __len__(self) -> int:
        return len(self._primary)

    def __contains__(self, anchor_id: object) -> bool:
        return anchor_id in self._primary

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self._primary.values())
