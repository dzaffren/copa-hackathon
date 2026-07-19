"""Anchor data model + AnchorIndex — the widened, doc-class-aware citation
foundation that supersedes `engine/clauses.py::ClauseIndex`.

This module is the core types + index only. The three segmenter strategies
(`structured-rules`, `semi-structured`, `prose`) are registered here by later
Tasks 3-5 via `SegmenterRegistry.register(...)`; on import this module ships an
EMPTY registry so `segment(...)` will raise `UnknownDocClassError` for any
doc_class until a strategy is installed. See
`docs/specs/workstream-brain/spec-engine-anchor-segmentation.md`.

Invariants every future segmenter MUST satisfy — enforced at build time via
`verify_substring(...)`:

- `anchor.text` is a LITERAL substring of the source markdown. No paraphrase,
  no normalisation, no LLM-quoted text. This is the verbatim-citation guardrail
  the whole knowledge-graph engine relies on.
- `anchor_id` is unique within an `AnchorIndex` (duplicates raise `ValueError`
  at construction — a loud failure rather than silently picking one).
- `AnchorIndex.get()` returns `None` on miss (never raises), matching the
  contract of `ClauseIndex.get()` today.
"""

from __future__ import annotations

from typing import Callable, Literal, Optional, TypedDict


class Anchor(TypedDict):
    """A verbatim, code-verified passage of source markdown, addressable by
    `anchor_id`.

    `heading_path`, `page_span`, and `parent_anchor` are marked "Optional" in
    the spec's Data Model — meaning a strategy may leave them empty/`None`.
    The fields themselves are ALWAYS present on the TypedDict (empty list or
    `None`), matching how `engine.clauses.ClauseEntry` handles optional fields.
    """

    anchor_id: str
    anchor_label: str
    text: str
    doc_class: Literal["structured-rules", "semi-structured", "prose"]
    document_id: str
    heading_path: list[str]
    page_span: Optional[tuple[int, int]]
    parent_anchor: Optional[str]


class AnchorCitation(TypedDict):
    """The citation shape carried on `Connection` / `UnsupportedConnection`.

    A widened `ClauseCitation`: keys the anchor by `anchor_id` and carries a
    UI-render label plus the verbatim text and `doc_class` for badge/filtering.
    """

    anchor_id: str
    anchor_label: str
    text: str
    doc_class: str


class AnchorTextNotFoundError(Exception):
    """Raised by `verify_substring` when an anchor's `text` is not a literal
    substring of its source markdown — the verbatim-citation guardrail every
    segmenter MUST satisfy before returning anchors.
    """


class UnknownDocClassError(Exception):
    """Raised by `segment(...)` when no `SegmenterFn` has been registered for
    the supplied `doc_class`. On import this module has an empty registry;
    Tasks 3-5 register the real strategies.
    """


def verify_substring(anchor: Anchor, source_markdown: str) -> None:
    """Raise `AnchorTextNotFoundError` if `anchor["text"]` is not a literal
    substring of `source_markdown`.

    The message names the offending `anchor_id`, echoes the first 80 chars of
    the anchor text, and reports the source-markdown length — enough for a
    human to diagnose without dumping megabytes into the log.
    """
    text = anchor["text"]
    if text in source_markdown:
        return

    preview = text[:80]
    raise AnchorTextNotFoundError(
        f"Anchor {anchor['anchor_id']!r} text not found in source markdown "
        f"(first 80 chars: {preview!r}; source markdown was "
        f"{len(source_markdown)} chars long)."
    )


class AnchorIndex:
    """Read-only, verbatim anchor lookup keyed by `anchor_id`.

    Mirrors `engine.clauses.ClauseIndex`:
    - O(1) `get(anchor_id) -> Optional[Anchor]`; returns `None` (never raises)
      on miss — the same contract downstream validators depend on.
    - `all()` returns every anchor in insertion order — the order the
      segmenters emitted them, which for document-order strategies is
      document order. Freezing traces relies on this stability.
    - `by_document(document_id)` returns the subset for one document, again in
      insertion order. Unknown `document_id` yields an empty list.

    Construction is strict: duplicate `anchor_id`s raise `ValueError` rather
    than silently over-writing. Same "flag for human" principle as
    `ClausePrimaryIndexCollisionError`.
    """

    def __init__(self, anchors: list[Anchor]) -> None:
        primary: dict[str, Anchor] = {}
        for anchor in anchors:
            anchor_id = anchor["anchor_id"]
            if anchor_id in primary:
                raise ValueError(
                    f"Duplicate anchor_id {anchor_id!r} in AnchorIndex — every "
                    f"anchor_id must be unique. Two anchors emitted for the "
                    f"same id likely means a segmenter double-emitted or two "
                    f"documents collided on a shared shortname."
                )
            primary[anchor_id] = anchor
        self._primary = primary

    def get(self, anchor_id: str) -> Optional[Anchor]:
        """Fetch an anchor verbatim; `None` if `anchor_id` is unknown."""
        return self._primary.get(anchor_id)

    def all(self) -> list[Anchor]:
        """Every anchor, in insertion (document) order."""
        return list(self._primary.values())

    def by_document(self, document_id: str) -> list[Anchor]:
        """Every anchor whose `document_id` matches, in insertion order.

        Unknown `document_id` yields an empty list.
        """
        return [
            anchor
            for anchor in self._primary.values()
            if anchor["document_id"] == document_id
        ]

    def __len__(self) -> int:
        return len(self._primary)

    def __contains__(self, anchor_id: object) -> bool:
        return anchor_id in self._primary

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self._primary.values())


# ---------------------------------------------------------------------------
# Segmenter registry.
#
# A `SegmenterFn` takes (document_id, source_markdown) and returns a list of
# Anchor records whose `text` fields satisfy the verify_substring invariant.
# The module-level `_REGISTRY` is EMPTY on import — Tasks 3-5 register the
# real strategies. `segment(...)` looks up the registered function and calls
# it; an unregistered doc_class raises `UnknownDocClassError`.

SegmenterFn = Callable[[str, str], list[Anchor]]


class SegmenterRegistry:
    """A dispatch table from `doc_class` to `SegmenterFn`.

    The engine ships one module-level registry (`_REGISTRY`) but the class is
    public so tests can instantiate isolated registries without polluting the
    module state.
    """

    def __init__(self) -> None:
        self._fns: dict[str, SegmenterFn] = {}

    def register(self, doc_class: str, fn: SegmenterFn) -> None:
        """Install (or replace) the segmenter for `doc_class`."""
        self._fns[doc_class] = fn

    def get(self, doc_class: str) -> Optional[SegmenterFn]:
        """Return the registered `SegmenterFn`, or `None` if none is
        registered for `doc_class`.
        """
        return self._fns.get(doc_class)


_REGISTRY = SegmenterRegistry()


def segment(
    document_id: str,
    source_markdown: str,
    doc_class: str,
) -> list[Anchor]:
    """Dispatch to the segmenter registered for `doc_class`.

    Raises `UnknownDocClassError` when no strategy is registered — the case
    every test in this module exercises on the empty default registry.
    """
    fn = _REGISTRY.get(doc_class)
    if fn is None:
        raise UnknownDocClassError(
            f"No segmenter registered for doc_class {doc_class!r}. Register "
            f"one via `engine.anchors._REGISTRY.register(...)` — Tasks 3-5 of "
            f"the anchor-segmentation spec install `structured-rules`, "
            f"`semi-structured`, and `prose`."
        )
    return fn(document_id, source_markdown)
