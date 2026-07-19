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

import re
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


# ---------------------------------------------------------------------------
# Task 3: structured-rules strategy — wraps `engine.clauses.segment_clauses`.
#
# BNM policy documents (RMiT, Outsourcing, OpRes, etc.) go through this path
# UNCHANGED. The segmenter is a thin re-wrapper: `segment_clauses` is the same
# deterministic rule-primary parser `ClauseIndex` uses today, so every emitted
# anchor's `text` is byte-identical to the clause text `ClauseIndex.get()`
# returns for the same clause number. The Anchor wrapper adds only
# metadata (`doc_class`, `anchor_id`, `anchor_label`, empty `heading_path`).


class UnknownDocumentIdError(ValueError):
    """Raised when `structured_rules_segment` is called with a `document_id`
    that has no entry in `engine.clauses.POLICY_SHORT_NAMES`.

    Structured-rules anchor_ids follow the canonical BNM shape
    ``"{PolicyShortName} {clause_number}"`` (e.g. ``"RMiT 17.1"``). The
    shortname must come from `POLICY_SHORT_NAMES` — the segmenter never
    fabricates one. Add the document to `POLICY_SHORT_NAMES` (or use a
    different `doc_class`) to fix.
    """


def structured_rules_segment(
    document_id: str,
    source_markdown: str,
) -> list[Anchor]:
    """Segment a BNM-style structured-rules document into Anchor records.

    Delegates to `engine.clauses.segment_clauses` — the same deterministic
    parser that backs `ClauseIndex` today. Each resulting `ClauseEntry` is
    wrapped as an `Anchor` with `anchor_id = "{PolicyShortName} {clause_number}"`
    (the canonical BNM citation shape). `heading_path` is empty and `page_span`
    is `None` — structured rules don't carry either.

    `verify_substring` is called on every emitted anchor as the verbatim-citation
    guardrail. Because `segment_clauses` slices clause text as a literal
    substring of `source_markdown`, this always passes; the assertion is a
    belt-and-braces check that a future refactor of `clauses.py` cannot silently
    break the invariant.

    `document_id` is interpreted as the POLICY_SHORT_NAMES key (what `clauses.py`
    internally calls `policy_id`) — e.g. `"rmit"`, `"outsourcing"`, `"opres"`.
    An unknown key raises `UnknownDocumentIdError` rather than fabricating a
    shortname or letting a bare `KeyError` bubble up.
    """
    # Local imports keep engine/anchors.py importable in test envs that stub
    # out engine.clauses, and avoid a circular import if clauses.py grows to
    # reference Anchor in future.
    from engine.clauses import POLICY_SHORT_NAMES, segment_clauses

    if document_id not in POLICY_SHORT_NAMES:
        raise UnknownDocumentIdError(
            f"Unknown document_id {document_id!r} for structured-rules "
            f"segmentation — no entry in engine.clauses.POLICY_SHORT_NAMES. "
            f"Add a shortname mapping (or use a different doc_class)."
        )

    entries = segment_clauses(
        markdown=source_markdown,
        document_id=document_id,
        policy_id=document_id,
        source="published",
    )

    anchors: list[Anchor] = []
    for entry in entries.values():
        # `clause_number` on a ClauseEntry is already the canonical
        # "{PolicyShortName} {bare_number}" (segment_clauses handles the join
        # via POLICY_SHORT_NAMES) — reuse it as anchor_id directly so BNM
        # callers see the exact same citation key they read today.
        canonical = entry["clause_number"]
        anchor: Anchor = {
            "anchor_id": canonical,
            "anchor_label": canonical,
            "text": entry["text"],
            "doc_class": "structured-rules",
            "document_id": document_id,
            "heading_path": [],
            "page_span": None,
            "parent_anchor": entry["parent"],
        }
        verify_substring(anchor, source_markdown)
        anchors.append(anchor)

    return anchors


# ---------------------------------------------------------------------------
# Task 4: semi-structured strategy — deterministic markdown-heading walker.
#
# Handles documents like MAS Notice 637, BoE Chapter 3, and BCBS papers whose
# structure is a mix of markdown headings (`#`, `##`, `###`) and numbered
# paragraphs (`20.1`, `20.3(a)`, `4.4 Title`). One `Anchor` per LEAF section —
# a heading that has no further-nested children. No LLM calls; regex + a small
# tree-walk. Every emitted anchor's `text` is a literal substring of the source
# markdown (checked via `verify_substring`).

# Markdown heading like `## 7.3 Standardised Approach`. `level` is 1..6 based
# on the number of leading `#`s.
_MARKDOWN_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

# Numbered-list-as-heading. Captures dot-separated numeric paths like
# `20.1`, `7.3.15`, `20.3(a)`, `4.4(i)`. The trailing `(alpha|roman)` is
# optional and, when present, is part of the numeric path — BCBS uses
# `20.3(a)` as a leaf citation. A "title" is anything after the number on
# the same line (may be empty).
_NUMBERED_HEADING_RE = re.compile(
    r"^(?P<num>\d+(?:\.\d+)*(?:\([a-z]+|\([ivxlcdm]+)?\)?)"
    r"(?:\s+(?P<title>\S.*?))?\s*$",
    re.IGNORECASE,
)

# Standalone alpha/roman bullet like `(a)`, `(i)`, `(iv)`. Emitted as a
# child level of the enclosing numeric heading.
_ALPHA_ROMAN_HEADING_RE = re.compile(
    r"^\((?P<key>[a-z]+|[ivxlcdm]+)\)(?:\s+(?P<title>\S.*?))?\s*$",
    re.IGNORECASE,
)


def _numeric_depth(num_path: str) -> int:
    """Depth of a dot-separated numeric path, counting sub-item parens as +1.

    `"20"` → 1, `"20.3"` → 2, `"20.3(a)"` → 3, `"7.3.15"` → 3.
    """
    # Strip the `(x)` suffix first, count it as +1 if present.
    paren_bonus = 1 if "(" in num_path else 0
    core = num_path.split("(", 1)[0]
    return core.count(".") + 1 + paren_bonus


class _Heading:
    """A parsed heading node during the semi-structured walk."""

    __slots__ = ("level", "num_path", "title", "start", "content_start", "children")

    def __init__(
        self,
        level: int,
        num_path: str,
        title: str,
        start: int,
        content_start: int,
    ) -> None:
        self.level = level
        self.num_path = num_path  # numeric key ("7.3.15") or "" for markdown-only
        self.title = title  # heading label without `#`s or numeric prefix
        self.start = start  # byte offset of heading line in source
        self.content_start = content_start  # byte offset AFTER the heading line
        self.children: list[_Heading] = []


def _strip_hashes(title: str) -> str:
    """Strip leading `#` characters and whitespace from a heading string.

    `"# Section 7 Credit Risk"` → `"Section 7 Credit Risk"`. Used to build
    `heading_path` labels without markdown syntax noise.
    """
    return title.lstrip("#").strip()


def _parse_semi_structured(source_markdown: str) -> list[_Heading]:
    """Parse the source into a FLAT list of headings in document order, each
    with `level` set to the nesting level (1 = top, larger = deeper).

    For markdown headings `#`/`##`/`###`, level = number of hashes.
    For numbered headings (`20.1`, `20.3(a)`), level = numeric depth + a
    large offset so numbered leaves nest under any markdown ancestor.
    """
    lines = source_markdown.split("\n")
    headings: list[_Heading] = []

    # Track byte offset for each line so we can slice text later.
    offsets: list[int] = []
    running = 0
    for line in lines:
        offsets.append(running)
        running += len(line) + 1  # +1 for the newline we split on

    # Offset that pushes numbered headings BELOW any markdown heading. We
    # reserve levels 1..6 for markdown; numbered depth 1 becomes level 7,
    # depth 2 becomes level 8, etc. This lets a `##` markdown heading contain
    # a `20.1` numbered child without conflict.
    NUMBERED_OFFSET = 6

    for i, raw in enumerate(lines):
        line = raw.rstrip()
        if not line:
            continue

        md_match = _MARKDOWN_HEADING_RE.match(line)
        if md_match:
            hashes, title = md_match.groups()
            level = len(hashes)
            start = offsets[i]
            content_start = offsets[i + 1] if i + 1 < len(offsets) else running
            # A markdown heading whose title STARTS with a numeric path
            # (`## 7.3 Standardised Approach`) carries a citation key — pull
            # the number out so the leaf detector treats it as part of the
            # numeric hierarchy. Otherwise it stays a bare markdown ancestor.
            inner_num_match = _NUMBERED_HEADING_RE.match(title.strip())
            num_path = ""
            heading_title = title.strip()
            if inner_num_match:
                num_path = inner_num_match.group("num")
                heading_title = (inner_num_match.group("title") or "").strip()
            headings.append(
                _Heading(
                    level=level,
                    num_path=num_path,
                    title=heading_title,
                    start=start,
                    content_start=content_start,
                )
            )
            continue

        num_match = _NUMBERED_HEADING_RE.match(line)
        if num_match:
            num_path = num_match.group("num")
            title = (num_match.group("title") or "").strip()
            level = NUMBERED_OFFSET + _numeric_depth(num_path)
            start = offsets[i]
            content_start = offsets[i + 1] if i + 1 < len(offsets) else running
            headings.append(
                _Heading(
                    level=level,
                    num_path=num_path,
                    title=title,
                    start=start,
                    content_start=content_start,
                )
            )
            continue

        alpha_match = _ALPHA_ROMAN_HEADING_RE.match(line)
        if alpha_match:
            key = alpha_match.group("key")
            title = (alpha_match.group("title") or "").strip()
            # Bare `(a)` bullets attach one level below the deepest numbered
            # ancestor seen so far — if none, treat as a top-level numbered
            # entry. Encode the numeric_path by prefixing with the ancestor
            # so anchor_ids remain unique across the doc.
            deepest_numbered = None
            for prev in reversed(headings):
                if prev.num_path:
                    deepest_numbered = prev
                    break
            if deepest_numbered is None:
                num_path = f"({key})"
                level = NUMBERED_OFFSET + 1
            else:
                num_path = f"{deepest_numbered.num_path}({key})"
                level = deepest_numbered.level + 1
            start = offsets[i]
            content_start = offsets[i + 1] if i + 1 < len(offsets) else running
            headings.append(
                _Heading(
                    level=level,
                    num_path=num_path,
                    title=title,
                    start=start,
                    content_start=content_start,
                )
            )
            continue

    return headings


def _is_numeric_descendant(child_path: str, parent_path: str) -> bool:
    """True iff `child_path`'s numbering is strictly nested under `parent_path`.

    `("7.3.15", "7.3")` → True; `("20.3(a)", "20.3")` → True;
    `("20.3(a)", "20.2")` → False; `("7.3", "7.3")` → False (same, not deeper).
    """
    if not parent_path or not child_path or child_path == parent_path:
        return False
    # Paren-sub-item under its bare number: `20.3(a)` under `20.3`.
    if child_path.startswith(parent_path + "("):
        return True
    # Deeper dot path: `7.3.15` under `7.3` (guard against `7.30` matching).
    if child_path.startswith(parent_path + "."):
        return True
    return False


def _is_child(child: "_Heading", parent: "_Heading") -> bool:
    """True iff `child` is nested under `parent` in the mixed markdown/numeric
    hierarchy.

    Cases:
    - both markdown: child hash-count > parent hash-count.
    - both numbered: `child.num_path` is a numeric descendant of `parent.num_path`.
    - parent markdown, child numbered: always True (numeric headings live under
      the nearest markdown heading; a shallower markdown heading closes the
      section via `_next_boundary`).
    - parent numbered, child markdown: never True (a `##` heading closes any
      open numbered section rather than nesting under it).
    """
    if parent.num_path == "" and child.num_path == "":
        return child.level > parent.level
    if parent.num_path != "" and child.num_path != "":
        return _is_numeric_descendant(child.num_path, parent.num_path)
    if parent.num_path == "" and child.num_path != "":
        return True
    return False


def _identify_leaves(headings: list[_Heading]) -> list[int]:
    """Return the indices of headings that have no descendant in the mixed
    markdown/numeric hierarchy — i.e. leaves of the nesting tree.

    Walks forward from each heading until it hits a boundary (a heading that
    is NOT its child). If any heading strictly before that boundary is a
    descendant, the current heading is an internal node.
    """
    leaves: list[int] = []
    n = len(headings)
    for i, h in enumerate(headings):
        has_child = False
        for j in range(i + 1, n):
            other = headings[j]
            if _is_child(other, h):
                has_child = True
                break
            # A non-child that is also not deeper-than-h closes h's section.
            if not _is_child(other, h):
                # We can't `break` blindly: `20.3(a)` may be followed by
                # `20.3(b)` — both are siblings, and neither is a child of
                # `20.2`. But `20.3(b)` is also not a child of `20.2`. So
                # keep scanning past non-children as long as they are also
                # not shallower ancestors. Simpler rule: keep scanning until
                # we find a child OR we find a heading that is shallower/
                # sibling of h (which closes h's block).
                if _closes_block(other, h):
                    break
        if not has_child:
            leaves.append(i)
    return leaves


def _closes_block(other: "_Heading", h: "_Heading") -> bool:
    """True iff encountering `other` closes the block opened by `h` — i.e.
    `other` is a same-level sibling or a shallower ancestor.

    A `20.3(a)` after `20.2` closes `20.2`'s block (both are at depth 2 in
    the numeric family — `20.3(a)`'s parent-numeric is `20.3`, a sibling of
    `20.2`). A `## 8` after `## 7` closes `## 7`. A `# Chapter 8` after
    `## 7.3` closes `## 7.3`.
    """
    # Markdown vs markdown: `other` closes h if `other.level <= h.level`.
    if h.num_path == "" and other.num_path == "":
        return other.level <= h.level
    # Numbered vs numbered: `other` closes h if the LCP of their num_paths is
    # a strict prefix of h.num_path (i.e. they don't share h.num_path as an
    # ancestor). Equivalently: `other` is NOT a descendant of h.
    if h.num_path and other.num_path:
        return not _is_numeric_descendant(other.num_path, h.num_path)
    # Numbered h, markdown other: any markdown heading closes a numbered block.
    if h.num_path and other.num_path == "":
        return True
    # Markdown h, numbered other: doesn't close (numbered lives inside markdown).
    return False


def _heading_path_labels(headings: list[_Heading], leaf_index: int) -> list[str]:
    """Build the ancestor label chain for a leaf, most-general first.

    Walks backwards from the leaf, keeping only headings for which the leaf is
    a descendant (per `_is_child`). Header prefixes like `#`/`##` are stripped;
    numeric prefixes are joined with the title so downstream UI sees
    `"Section 7 Credit Risk"` / `"7.3 Standardised Approach"`.
    """
    leaf = headings[leaf_index]
    ancestors: list[_Heading] = []
    for j in range(leaf_index - 1, -1, -1):
        candidate = headings[j]
        if _is_child(leaf, candidate):
            # Keep only the CLOSEST ancestor at each layer — skip a candidate
            # that is itself a descendant of an already-collected ancestor at
            # the same layer. Simpler test: after collecting, only keep those
            # whose num_path/level chain is monotonically less nested.
            ancestors.append(candidate)
    # Deduplicate: for two collected ancestors A and B where B is a descendant
    # of A, we want BOTH (A is a real ancestor, B is a real ancestor). Keep
    # only the ones that form the direct ancestor chain up from leaf.
    ancestors.reverse()

    # Filter to the direct ancestor chain: walking from leaf, take each
    # closest strictly-shallower ancestor.
    chain: list[_Heading] = []
    current = leaf
    for anc in reversed(ancestors):
        if _is_child(current, anc):
            chain.append(anc)
            current = anc
    chain.reverse()

    labels: list[str] = []
    for anc in chain:
        if anc.num_path:
            label = f"{anc.num_path} {anc.title}".strip() if anc.title else anc.num_path
        else:
            label = _strip_hashes(anc.title)
        labels.append(label)
    return labels


def _text_for_leaf(
    source_markdown: str,
    headings: list[_Heading],
    leaf_index: int,
) -> str:
    """Slice the passage that belongs to `headings[leaf_index]` — everything
    from the byte AFTER the heading line up to (but not including) the next
    heading that CLOSES the leaf's block (per `_closes_block`, or any child
    heading — leaves shouldn't have children, but be defensive). Result is a
    literal substring of the source.
    """
    leaf = headings[leaf_index]
    n = len(headings)
    end = len(source_markdown)
    for j in range(leaf_index + 1, n):
        other = headings[j]
        if _closes_block(other, leaf) or _is_child(other, leaf):
            end = other.start
            break
    passage = source_markdown[leaf.content_start : end]
    # Trim leading/trailing whitespace so the anchor doesn't dangle blank
    # lines into either neighbour. `.strip()` keeps the passage a literal
    # substring because we only shrink the edges.
    return passage.strip()


def semi_structured_segment(
    document_id: str,
    source_markdown: str,
    *,
    shortname: Optional[str] = None,
    section_mark: bool = False,
) -> list[Anchor]:
    """Segment a semi-structured document (markdown headings + numbered
    paragraphs) into `Anchor` records — one per LEAF section.

    Deterministic Python parsing. NO LLM calls. Handles three heading kinds:

    - Markdown `#`, `##`, `###` — level = number of hashes.
    - Numbered-list-as-heading — `1.1`, `7.3.15`, `20.3(a)`, `4.4 Title`.
    - Standalone alpha/roman bullets — `(a)`, `(ii)` — attached one level
      below the deepest numbered ancestor.

    `anchor_id` shape is `"{shortname} {numeric-path}"` (when `shortname` is
    provided) with an optional `§` between shortname and path when
    `section_mark=True`. If `shortname is None`, `document_id` is used as
    the prefix — good enough for callers that don't need pretty citations.

    `heading_path` records the enclosing headings, most-general first, e.g.
    `["Section 7 Credit Risk", "7.3 Standardised Approach"]` for a MAS 637
    §7.3.15 leaf. Header prefixes like `#` are stripped from labels.

    Every emitted anchor's `text` is verified as a literal substring of
    `source_markdown` via `verify_substring` — the verbatim-citation guardrail
    the whole KG engine relies on.
    """
    headings = _parse_semi_structured(source_markdown)
    if not headings:
        return []

    prefix = shortname if shortname is not None else document_id
    join_sep = " §" if section_mark else " "

    anchors: list[Anchor] = []
    for leaf_index in _identify_leaves(headings):
        leaf = headings[leaf_index]
        # Only emit anchors for headings that have a numeric identity — a
        # bare markdown heading like `# Chapter 3` with no numbered children
        # has no citation key, so skip it. If a caller really wants to cite
        # a chapter overview, promote it to a numbered heading upstream.
        if not leaf.num_path:
            continue

        numeric_path = leaf.num_path
        anchor_id = f"{prefix}{join_sep}{numeric_path}"
        text = _text_for_leaf(source_markdown, headings, leaf_index)
        heading_path = _heading_path_labels(headings, leaf_index)

        anchor: Anchor = {
            "anchor_id": anchor_id,
            "anchor_label": anchor_id,
            "text": text,
            "doc_class": "semi-structured",
            "document_id": document_id,
            "heading_path": heading_path,
            "page_span": None,
            "parent_anchor": None,
        }
        verify_substring(anchor, source_markdown)
        anchors.append(anchor)

    return anchors


_REGISTRY = SegmenterRegistry()
_REGISTRY.register("structured-rules", structured_rules_segment)
_REGISTRY.register("semi-structured", semi_structured_segment)


def segment(
    document_id: str,
    source_markdown: str,
    doc_class: str,
    registry: Optional[SegmenterRegistry] = None,
) -> list[Anchor]:
    """Dispatch to the segmenter registered for `doc_class`.

    Uses the module-level `_REGISTRY` by default (which has `structured-rules`
    installed at import time — see Task 3). Tests can inject their own
    `registry` to keep module state clean.

    Raises `UnknownDocClassError` when no strategy is registered for
    `doc_class` on the resolved registry.
    """
    active_registry = registry if registry is not None else _REGISTRY
    fn = active_registry.get(doc_class)
    if fn is None:
        raise UnknownDocClassError(
            f"No segmenter registered for doc_class {doc_class!r}. Register "
            f"one via `engine.anchors._REGISTRY.register(...)` — Tasks 3-5 of "
            f"the anchor-segmentation spec install `structured-rules`, "
            f"`semi-structured`, and `prose`."
        )
    return fn(document_id, source_markdown)
