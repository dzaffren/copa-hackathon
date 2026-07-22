# Anchor Segmentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the engine citable, verbatim anchors for non-BNM documents by adopting an `AnchorIndex` architecture with a doc-class-routed segmenter registry, where non-BNM docs use LLM boundary-detection + deterministic verbatim slicing.

**Architecture:** Two segmentation lanes feed one `AnchorIndex`. BNM docs stay on the existing deterministic regex path (`structured-rules`, offline, no model). Non-BNM docs (`legislative`/`framework`) use a new segmenter where the model emits only `{anchor_label, starts_with, parent}` and deterministic code slices verbatim text and gates it with `verify_substring`. The finder→critic loop consumes the unified index unchanged.

**Tech Stack:** Python 3.13, pytest, `engine.llm.call_chat` (Anthropic Messages API on Azure Foundry). No new dependencies.

## Global Constraints

- **Verbatim guarantee:** every `anchor["text"]` MUST be a literal substring of the source markdown; enforced by `verify_substring`. The model never produces citation text — only boundaries.
- **No new pip dependencies** (spec: reuses existing `call_chat` + stdlib `re`).
- **CI never calls a model:** all segmenter tests inject a stubbed boundary function; the committed `anchor-index.json` is what CI reads.
- **BNM must not regress:** BNM anchor_ids equal today's clause_numbers (`"RMiT 10.16"`); committed `connection-trace-*.json` and PR #47's `test_all_committed_traces_still_resolve` must stay green.
- **UTF-8 always:** any `write_text` of document/markdown text passes `encoding="utf-8"` (clause text carries U+2212, en-dashes).
- **Conventional Commits**, one logical change per commit. Never commit to `main`/`dzaf/main` directly — this work lands on a feature branch.

---

### Task 1: Anchor data model + AnchorIndex

Adopt the citation-substrate skeleton onto `dzaf/main`, widening `doc_class` to include the new classes. This is the foundation every later task consumes.

**Files:**

- Create: `engine/anchors.py`
- Test: `engine/tests/test_anchors.py`

**Interfaces:**

- Consumes: nothing (foundation).
- Produces:
  - `Anchor` TypedDict: `{anchor_id: str, anchor_label: str, text: str, doc_class: str, document_id: str, heading_path: list[str], page_span: Optional[tuple[int,int]], parent_anchor: Optional[str]}`
  - `AnchorCitation` TypedDict: `{anchor_id: str, anchor_label: str, text: str, doc_class: str}`
  - `DOC_CLASSES: tuple[str, ...]` = `("structured-rules", "legislative", "framework", "prose")`
  - `class AnchorTextNotFoundError(Exception)`
  - `verify_substring(anchor: Anchor, source_markdown: str) -> None`
  - `class AnchorIndex` with `__init__(self, anchors: list[Anchor])`, `get(anchor_id: str) -> Optional[Anchor]`, `all() -> list[Anchor]`, `by_document(document_id: str) -> list[Anchor]`, `__len__`, `__contains__`, `__iter__`

- [ ] **Step 1: Write the failing test**

```python
# engine/tests/test_anchors.py
import pytest

from engine.anchors import (
    DOC_CLASSES,
    AnchorIndex,
    AnchorTextNotFoundError,
    verify_substring,
)


def _anchor(anchor_id="EU AI Act Article 1", text="Providers shall ensure",
            doc_class="legislative", document_id="eu-ai-act"):
    return {
        "anchor_id": anchor_id,
        "anchor_label": anchor_id.split(" ", 2)[-1],
        "text": text,
        "doc_class": doc_class,
        "document_id": document_id,
        "heading_path": [],
        "page_span": None,
        "parent_anchor": None,
    }


def test_doc_classes_include_legislative_and_framework():
    assert "legislative" in DOC_CLASSES
    assert "framework" in DOC_CLASSES
    assert "structured-rules" in DOC_CLASSES
    assert "prose" in DOC_CLASSES


def test_verify_substring_passes_when_text_is_a_substring():
    source = "... Providers shall ensure that the technical ..."
    verify_substring(_anchor(text="Providers shall ensure"), source)  # no raise


def test_verify_substring_raises_when_text_absent():
    with pytest.raises(AnchorTextNotFoundError) as exc:
        verify_substring(_anchor(text="not present here"), "totally different source")
    assert "EU AI Act Article 1" in str(exc.value)


def test_index_get_returns_none_on_miss():
    idx = AnchorIndex([_anchor()])
    assert idx.get("nope") is None
    assert idx.get("EU AI Act Article 1") is not None


def test_index_by_document_filters_in_insertion_order():
    a = _anchor(anchor_id="EU AI Act Article 1", document_id="eu-ai-act")
    b = _anchor(anchor_id="RMiT 10.16", document_id="rmit-v2-2025",
                doc_class="structured-rules")
    idx = AnchorIndex([a, b])
    got = idx.by_document("eu-ai-act")
    assert [x["anchor_id"] for x in got] == ["EU AI Act Article 1"]
    assert len(idx) == 2
    assert "RMiT 10.16" in idx


def test_duplicate_anchor_id_raises_at_construction():
    with pytest.raises(ValueError):
        AnchorIndex([_anchor(), _anchor()])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest engine/tests/test_anchors.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'engine.anchors'`

- [ ] **Step 3: Write minimal implementation**

```python
# engine/anchors.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest engine/tests/test_anchors.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add engine/anchors.py engine/tests/test_anchors.py
git commit -m "feat(engine): add Anchor data model + AnchorIndex"
```

---

### Task 2: SegmenterRegistry

A dispatch table from `doc_class` to a segmenter function. Kept separate from Task 1 so it can be tested independently and so the LLM segmenter (Task 3) has a registration target.

**Files:**

- Modify: `engine/anchors.py` (append)
- Test: `engine/tests/test_anchors.py` (append)

**Interfaces:**

- Consumes: `Anchor` (Task 1).
- Produces:
  - `SegmenterFn = Callable[[str, str], list[Anchor]]` (args: `document_id`, `source_markdown`)
  - `class UnknownDocClassError(Exception)`
  - `class SegmenterRegistry` with `register(doc_class: str, fn: SegmenterFn) -> None`, `get(doc_class: str) -> SegmenterFn` (raises `UnknownDocClassError` on miss)

- [ ] **Step 1: Write the failing test**

```python
# append to engine/tests/test_anchors.py
from engine.anchors import SegmenterRegistry, UnknownDocClassError


def test_registry_dispatches_registered_class():
    reg = SegmenterRegistry()
    reg.register("legislative", lambda doc_id, md: [_anchor()])
    fn = reg.get("legislative")
    assert fn("eu-ai-act", "source")[0]["anchor_id"] == "EU AI Act Article 1"


def test_registry_raises_on_unknown_class():
    reg = SegmenterRegistry()
    with pytest.raises(UnknownDocClassError):
        reg.get("legislative")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest engine/tests/test_anchors.py -k registry -v`
Expected: FAIL with `ImportError: cannot import name 'SegmenterRegistry'`

- [ ] **Step 3: Write minimal implementation**

```python
# append to engine/anchors.py
from typing import Callable  # add to the existing typing import line

SegmenterFn = Callable[[str, str], list[Anchor]]


class UnknownDocClassError(Exception):
    """Raised by SegmenterRegistry.get when no strategy is registered for a
    doc_class."""


class SegmenterRegistry:
    """Dispatch table: doc_class -> SegmenterFn. Empty until strategies register."""

    def __init__(self) -> None:
        self._strategies: dict[str, SegmenterFn] = {}

    def register(self, doc_class: str, fn: SegmenterFn) -> None:
        self._strategies[doc_class] = fn

    def get(self, doc_class: str) -> SegmenterFn:
        fn = self._strategies.get(doc_class)
        if fn is None:
            raise UnknownDocClassError(
                f"No segmenter registered for doc_class {doc_class!r}. "
                f"Registered: {sorted(self._strategies)}"
            )
        return fn
```

Note: change the top-of-file import to `from typing import Callable, Optional, TypedDict`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest engine/tests/test_anchors.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add engine/anchors.py engine/tests/test_anchors.py
git commit -m "feat(engine): add SegmenterRegistry for doc-class dispatch"
```

---

### Task 3: LLM-boundary segmenter

The one genuinely new piece: a segmenter where the model emits only boundaries + labels, and deterministic code slices verbatim text and gates it. Reuses `_find_anchor_positions` from `clauses.py`. The model call is behind an injectable `boundary_fn` seam so tests never touch the network.

**Files:**

- Create: `engine/anchors_llm.py`
- Test: `engine/tests/test_anchors_llm.py`

**Interfaces:**

- Consumes: `Anchor`, `verify_substring` (Task 1); `engine.clauses._find_anchor_positions(markdown: str, snippet: str) -> list[int]`; `engine.llm.call_chat(deployment, system, user, max_tokens) -> str`.
- Produces:
  - `BoundaryFn = Callable[[str, str, str], list[dict]]` (args: `document_id`, `source_markdown`, `doc_class`; returns raw `[{anchor_label, starts_with, parent}]`)
  - `llm_boundary_segment(document_id: str, source_markdown: str, *, doc_class: str, shortname: str, boundary_fn: Optional[BoundaryFn] = None, dropped_report: Optional[list[dict]] = None) -> list[Anchor]`
  - `BOUNDARY_SYSTEM_PROMPT: str`

- [ ] **Step 1: Write the failing test**

```python
# engine/tests/test_anchors_llm.py
from engine.anchors import AnchorTextNotFoundError
from engine.anchors_llm import llm_boundary_segment

SOURCE = (
    "REGULATION (EU) 2024/1689\n\n"
    "Article 1\n\n"
    "This Regulation lays down harmonised rules on artificial intelligence.\n\n"
    "Article 2\n\n"
    "This Regulation applies to providers placing AI systems on the market.\n"
)


def _boundaries(document_id, source_markdown, doc_class):
    return [
        {"anchor_label": "Article 1",
         "starts_with": "This Regulation lays down harmonised rules",
         "parent": None},
        {"anchor_label": "Article 2",
         "starts_with": "This Regulation applies to providers",
         "parent": None},
    ]


def test_boundary_segment_produces_citable_verbatim_anchors():
    anchors = llm_boundary_segment(
        "eu-ai-act", SOURCE, doc_class="legislative",
        shortname="EU AI Act", boundary_fn=_boundaries,
    )
    assert [a["anchor_id"] for a in anchors] == [
        "EU AI Act Article 1", "EU AI Act Article 2"]
    # citable label
    assert anchors[0]["anchor_label"] == "Article 1"
    # verbatim: text is a real substring of the source
    for a in anchors:
        assert a["text"] in SOURCE
        assert a["text"].strip()
    assert anchors[0]["doc_class"] == "legislative"


def test_boundary_not_found_is_dropped_not_raised():
    def bad(document_id, source_markdown, doc_class):
        return [{"anchor_label": "Article 9",
                 "starts_with": "text that is absent from source",
                 "parent": None}]
    report: list[dict] = []
    anchors = llm_boundary_segment(
        "eu-ai-act", SOURCE, doc_class="legislative",
        shortname="EU AI Act", boundary_fn=bad, dropped_report=report,
    )
    assert anchors == []
    assert report and report[0]["reason"] == "not_found"
    assert report[0]["anchor_label"] == "Article 9"


def test_every_returned_anchor_passes_verify_substring():
    # Guard: llm_boundary_segment must never emit an anchor whose text is not a
    # substring — a defensive re-check on its own output.
    anchors = llm_boundary_segment(
        "eu-ai-act", SOURCE, doc_class="legislative",
        shortname="EU AI Act", boundary_fn=_boundaries,
    )
    from engine.anchors import verify_substring
    for a in anchors:
        verify_substring(a, SOURCE)  # must not raise
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest engine/tests/test_anchors_llm.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'engine.anchors_llm'`

- [ ] **Step 3: Write minimal implementation**

```python
# engine/anchors_llm.py
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

import json
from typing import Callable, Optional

from engine.anchors import Anchor, verify_substring
from engine.clauses import _find_anchor_positions
from engine.config import FINDER_CRITIC_DEPLOYMENT
from engine.llm import call_chat

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
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("boundary model did not return a JSON array")
    return data


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
        end = resolved[i + 1][1] if i + 1 < len(resolved) else len(source_markdown)
        text = source_markdown[start:end].strip()
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest engine/tests/test_anchors_llm.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add engine/anchors_llm.py engine/tests/test_anchors_llm.py
git commit -m "feat(engine): add LLM-boundary segmenter (non-BNM lane)"
```

---

### Task 4: Wrap the BNM regex segmenter as an AnchorIndex strategy

The existing `segment_clauses` returns `ClauseEntry` dicts keyed by clause_number. Wrap it to emit `Anchor` records with `doc_class="structured-rules"`, so both lanes produce the same shape. This keeps BNM offline and deterministic.

**Files:**

- Create: `engine/anchors_bnm.py`
- Test: `engine/tests/test_anchors_bnm.py`

**Interfaces:**

- Consumes: `Anchor` (Task 1); `engine.clauses.segment_clauses(markdown, document_id, policy_id, source, expected_clauses=None, dropped_report=None) -> dict[str, ClauseEntry]` where each `ClauseEntry` has keys `clause_number`, `text`, `heading`, `parent`, `document_id`.
- Produces: `structured_rules_segment(document_id: str, source_markdown: str, *, policy_id: str, source: str) -> list[Anchor]`

- [ ] **Step 1: Write the failing test**

```python
# engine/tests/test_anchors_bnm.py
from engine.anchors import verify_substring
from engine.anchors_bnm import structured_rules_segment

# Minimal BNM-shaped markdown: "10.1" then a sub-item.
BNM_MD = (
    "10 Governance\n\n"
    "10.1 A financial institution must establish a robust framework.\n\n"
    "10.2 The board shall oversee the framework.\n"
)


def test_structured_rules_emits_anchors_with_clause_number_ids():
    anchors = structured_rules_segment(
        "rmit-v2-2025", BNM_MD, policy_id="rmit", source="rmit.pdf")
    ids = {a["anchor_id"] for a in anchors}
    assert "RMiT 10.1" in ids
    assert "RMiT 10.2" in ids
    for a in anchors:
        assert a["doc_class"] == "structured-rules"
        assert a["document_id"] == "rmit-v2-2025"
        verify_substring(a, BNM_MD)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest engine/tests/test_anchors_bnm.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'engine.anchors_bnm'`

- [ ] **Step 3: Write minimal implementation**

```python
# engine/anchors_bnm.py
"""BNM structured-rules segmenter, adapted to the Anchor shape.

Wraps engine.clauses.segment_clauses (the deterministic regex parser, offline,
no model) so it emits Anchor records with doc_class="structured-rules". The
anchor_id is the canonical clause_number ("RMiT 10.1"), so BNM anchors keep the
exact keys today's clause_number-keyed traces and tests rely on — no regression.
"""
from __future__ import annotations

from typing import Optional

from engine.anchors import Anchor
from engine.clauses import segment_clauses


def structured_rules_segment(
    document_id: str,
    source_markdown: str,
    *,
    policy_id: str,
    source: str,
    dropped_report: Optional[list[dict]] = None,
) -> list[Anchor]:
    entries = segment_clauses(
        source_markdown, document_id, policy_id, source,
        dropped_report=dropped_report,
    )
    anchors: list[Anchor] = []
    for clause_number, entry in entries.items():
        anchors.append({
            "anchor_id": clause_number,
            "anchor_label": clause_number,
            "text": entry["text"],
            "doc_class": "structured-rules",
            "document_id": document_id,
            "heading_path": [entry["heading"]] if entry.get("heading") else [],
            "page_span": None,
            "parent_anchor": entry.get("parent"),
        })
    return anchors
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest engine/tests/test_anchors_bnm.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engine/anchors_bnm.py engine/tests/test_anchors_bnm.py
git commit -m "feat(engine): wrap BNM regex segmenter as structured-rules strategy"
```

---

### Task 5: doc_class in the document manifest

Declare a `doc_class` per document in `config.DOCUMENTS` — declared, not inferred. BNM entries → `structured-rules`; reference PDFs tagged per the spec table.

**Files:**

- Modify: `engine/config.py` (add `"doc_class"` to each `DOCUMENTS` entry and each reference entry)
- Test: `engine/tests/test_config.py` (append)

**Interfaces:**

- Consumes: `DOC_CLASSES` (Task 1).
- Produces: every `config.DOCUMENTS[*]` and reference-doc entry has a `"doc_class"` key drawn from `DOC_CLASSES`.

- [ ] **Step 1: Write the failing test**

```python
# append to engine/tests/test_config.py
from engine.anchors import DOC_CLASSES
from engine.config import DOCUMENTS


def test_every_document_declares_a_valid_doc_class():
    for document_id, doc in DOCUMENTS.items():
        assert "doc_class" in doc, f"{document_id} missing doc_class"
        assert doc["doc_class"] in DOC_CLASSES, (
            f"{document_id} has doc_class {doc['doc_class']!r} not in {DOC_CLASSES}")


def test_bnm_documents_are_structured_rules():
    # The nine BNM policy docs keep the deterministic offline lane.
    assert DOCUMENTS["rmit-v2-2025"]["doc_class"] == "structured-rules"
    assert DOCUMENTS["opres-v1-2025-draft"]["doc_class"] == "structured-rules"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest engine/tests/test_config.py -k doc_class -v`
Expected: FAIL with `KeyError` or assertion that `doc_class` is missing

- [ ] **Step 3: Write minimal implementation**

Add `"doc_class": "structured-rules",` to each of the nine BNM entries in `DOCUMENTS` (ai-dp-2025, rmit-v1-2023, rmit-v2-2025, outsourcing-v1-2019, bcm-v1-2022, opres-v1-2025-draft, recovery-planning-v1-2021, customer-info-v1-2025, open-finance-v1-2025-ed). Add `"doc_class"` to reference entries per the spec: `eu-ai-act` and `pdpa-2010` → `"legislative"`; `nist-ai-rmf`, `oecd-ai`, `basel-por-2021`, `mas-trm-2021`, `bcbs-239` → `"framework"`.

Example (one BNM entry):

```python
    "rmit-v2-2025": {
        "document_id": "rmit-v2-2025",
        "policy_id": "rmit",
        "doc_class": "structured-rules",  # ADD THIS LINE
        "source_path": CORPUS_DIR / "pd-rmit-nov25.pdf",
        # ... existing fields unchanged ...
    },
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest engine/tests/test_config.py -k doc_class -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add engine/config.py engine/tests/test_config.py
git commit -m "feat(engine): declare doc_class per document in manifest"
```

---

### Task 6: Migrate connections.py to AnchorIndex

Swap the finder→critic loop's citation substrate from `ClauseIndex` to `AnchorIndex`. This is largely yenmay's mechanical rename; the guardrail is identical, keyed by `anchor_id`. Because BNM anchor_ids equal old clause_numbers, committed traces and PR #47 tests stay green.

**Files:**

- Modify: `engine/connections.py` (type annotations `ClauseIndex` → `AnchorIndex`; `_cite`/`_validate_candidates` lookups use `anchor_index.get(id)`)
- Test: `engine/tests/test_connections.py` (existing tests must pass with an `AnchorIndex` fixture)

**Interfaces:**

- Consumes: `AnchorIndex`, `AnchorCitation` (Task 1).
- Produces: `find_connections(doc_a_id, doc_b_id, anchor_index: AnchorIndex, ...)` — same return shape `{"connections": [...], "unsupported": [...]}`.

- [ ] **Step 1: Write the failing test**

```python
# append to engine/tests/test_connections.py
from engine.anchors import AnchorIndex
from engine.connections import find_connections


def _bnm_anchor(anchor_id, text):
    return {"anchor_id": anchor_id, "anchor_label": anchor_id, "text": text,
            "doc_class": "structured-rules", "document_id": "rmit-v2-2025",
            "heading_path": [], "page_span": None, "parent_anchor": None}


def test_find_connections_accepts_anchor_index():
    index = AnchorIndex([
        _bnm_anchor("RMiT 10.16", "cryptography policy text"),
        _bnm_anchor("RMiT 10.55", "multi-factor authentication text"),
    ])

    def finder(a, b, idx):
        return [{"summary": "both require MFA", "label": "aligns-with",
                 "sentiment": None,
                 "source_anchors": ["RMiT 10.16"],
                 "target_anchors": ["RMiT 10.55"]}]

    def critic(a, b, idx, cands):
        return cands

    result = find_connections("rmit-v2-2025", "rmit-v2-2025", index,
                              finder_fn=finder, critic_fn=critic,
                              output_dir=None)
    assert len(result["connections"]) == 1
    conn = result["connections"][0]
    # verbatim text fetched from the index by id, not from the model
    assert conn["source_anchors"][0]["text"] == "cryptography policy text"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest engine/tests/test_connections.py -k anchor_index -v`
Expected: FAIL — `find_connections` still typed for `ClauseIndex` / uses `clause_number` keys / `source_clauses`

- [ ] **Step 3: Write minimal implementation**

Apply yenmay's `connections.py` changes (cherry-pick reference: `git show origin/yenmay/main:engine/connections.py`). Concretely: rename the parameter `clause_index` → `anchor_index`; import `from engine.anchors import AnchorCitation, AnchorIndex`; in `_validate_candidates`, read `candidate.get("source_anchors")` / `target_anchors`, resolve each id via `anchor_index.get(id)`, and build `AnchorCitation` in `_cite` by fetching `entry["text"]` and `entry["anchor_label"]`. Keep `_write_trace` and the loop order identical. Do NOT take yenmay's `anchors.py` regex strategies — this task only touches `connections.py`.

- [ ] **Step 4: Run the full connections + integrity suites**

Run: `.venv/bin/python -m pytest engine/tests/test_connections.py engine/tests/test_artifact_integrity.py engine/tests/test_taxonomy_traces.py -v`
Expected: PASS — including `test_all_committed_traces_still_resolve` (BNM anchor_ids unchanged)

- [ ] **Step 5: Commit**

```bash
git add engine/connections.py engine/tests/test_connections.py
git commit -m "refactor(engine): key finder/critic citations by AnchorIndex"
```

---

### Task 7: Build wiring — dispatch by doc_class, write anchor-index.json

Extend `build.py`'s per-document loop to dispatch to the registered segmenter by `doc_class`, run `verify_substring` on every anchor, and write `anchor-index.json`.

**Files:**

- Modify: `engine/build.py` (register the two live strategies; dispatch by `doc["doc_class"]`; write `anchor-index.json`)
- Test: `engine/tests/test_build.py` (append — with stubbed ingest + stubbed boundary_fn)

**Interfaces:**

- Consumes: `structured_rules_segment` (Task 4), `llm_boundary_segment` (Task 3), `SegmenterRegistry` (Task 2), `AnchorIndex` (Task 1).
- Produces: a built `anchor-index.json` (list of `Anchor` dicts) under the output dir.

- [ ] **Step 1: Write the failing test**

```python
# append to engine/tests/test_build.py
import json

from engine.build import build_anchor_index


def test_build_dispatches_by_doc_class(tmp_path):
    documents = {
        "rmit-v2-2025": {"document_id": "rmit-v2-2025", "policy_id": "rmit",
                         "doc_class": "structured-rules", "source_path": "x.pdf"},
        "eu-ai-act": {"document_id": "eu-ai-act", "policy_id": "eu-ai-act",
                      "doc_class": "legislative", "source_path": "y.pdf",
                      "shortname": "EU AI Act"},
    }
    md = {
        "rmit-v2-2025": "10.1 A financial institution must establish a framework.\n",
        "eu-ai-act": "Article 1\n\nThis Regulation lays down rules.\n",
    }

    def ingest(path):
        return md["rmit-v2-2025"] if str(path) == "x.pdf" else md["eu-ai-act"]

    def boundary(document_id, source_markdown, doc_class):
        return [{"anchor_label": "Article 1",
                 "starts_with": "This Regulation lays down rules",
                 "parent": None}]

    index = build_anchor_index(
        documents, ingest_fn=ingest, boundary_fn=boundary, output_dir=tmp_path)
    ids = {a["anchor_id"] for a in index.all()}
    assert "RMiT 10.1" in ids            # BNM lane
    assert "EU AI Act Article 1" in ids  # LLM lane
    written = json.loads((tmp_path / "anchor-index.json").read_text("utf-8"))
    assert len(written) == len(index)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest engine/tests/test_build.py -k dispatches -v`
Expected: FAIL with `ImportError: cannot import name 'build_anchor_index'`

- [ ] **Step 3: Write minimal implementation**

```python
# add to engine/build.py
import json
from pathlib import Path
from typing import Any, Callable, Optional

from engine.anchors import AnchorIndex, SegmenterRegistry, verify_substring
from engine.anchors_bnm import structured_rules_segment
from engine.anchors_llm import BoundaryFn, llm_boundary_segment
from engine.clauses import POLICY_SHORT_NAMES
from engine.ingest import ingest_document


def build_anchor_index(
    documents: dict[str, dict[str, Any]],
    *,
    ingest_fn: Callable[[Any], str] = ingest_document,
    boundary_fn: Optional[BoundaryFn] = None,
    output_dir: Optional[Path] = None,
) -> AnchorIndex:
    """Segment every document via its doc_class strategy into a single
    AnchorIndex, running verify_substring on every anchor, and (if output_dir)
    write anchor-index.json. BNM docs use the deterministic lane; legislative/
    framework docs use the LLM-boundary lane."""
    all_anchors = []
    for document_id, doc in documents.items():
        markdown = ingest_fn(doc["source_path"])
        doc_class = doc["doc_class"]
        if doc_class == "structured-rules":
            anchors = structured_rules_segment(
                document_id, markdown,
                policy_id=doc["policy_id"], source=str(doc["source_path"]))
        else:
            shortname = doc.get("shortname") or POLICY_SHORT_NAMES.get(
                doc["policy_id"], doc["policy_id"])
            anchors = llm_boundary_segment(
                document_id, markdown, doc_class=doc_class,
                shortname=shortname, boundary_fn=boundary_fn)
        for anchor in anchors:
            verify_substring(anchor, markdown)
        all_anchors.extend(anchors)

    index = AnchorIndex(all_anchors)
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "anchor-index.json").write_text(
            json.dumps(all_anchors, indent=2, ensure_ascii=False),
            encoding="utf-8")
    return index
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest engine/tests/test_build.py -k dispatches -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engine/build.py engine/tests/test_build.py
git commit -m "feat(engine): build anchor-index.json by doc_class dispatch"
```

---

### Task 8: Acceptance harness — coverage + verbatim + citable label

The measurable bar. One parametrized test per non-BNM doc, checking a built anchor set against a small ground-truth fixture. Since building requires the model, this task builds ONE non-BNM doc live (marked, opt-in) to produce a committed `anchor-index.json` slice, then the acceptance test reads that committed artifact — no model in CI.

**Files:**

- Create: `engine/tests/fixtures/ground_truth/eu-ai-act.json` (hand-authored top-level locators)
- Create: `engine/tests/test_anchor_coverage.py`
- Test: itself

**Interfaces:**

- Consumes: committed `data/artifacts/anchor-index.json` (produced by a live build, see Step 3); ground-truth fixture.
- Produces: the three-assertion acceptance gate.

- [ ] **Step 1: Write the ground-truth fixture**

```json
// engine/tests/fixtures/ground_truth/eu-ai-act.json
{
  "document_id": "eu-ai-act",
  "shortname": "EU AI Act",
  "coverage_floor": 0.8,
  "label_pattern": "^Article \\d+",
  "garbage_pattern": "\\d+\\.\\d+\\.\\d{4}",
  "top_level_locators": [
    "Article 1",
    "Article 2",
    "Article 3",
    "Article 4",
    "Article 5"
  ]
}
```

Note: `top_level_locators` is a representative sample from the Act's own table of contents; `coverage_floor` is pinned from measured reality after Step 3 (start at 0.80, adjust down with a note if the live build measures lower — never up to force a pass).

- [ ] **Step 2: Write the failing test**

```python
# engine/tests/test_anchor_coverage.py
import json
import re
from pathlib import Path

import pytest

from engine.config import REPO_ROOT

FIXTURES = Path(__file__).parent / "fixtures" / "ground_truth"
ANCHOR_INDEX = REPO_ROOT / "data" / "artifacts" / "anchor-index.json"
GROUND_TRUTHS = sorted(FIXTURES.glob("*.json"))


@pytest.fixture(scope="module")
def index():
    assert ANCHOR_INDEX.exists(), f"{ANCHOR_INDEX} missing — run the live build"
    return json.loads(ANCHOR_INDEX.read_text(encoding="utf-8"))


@pytest.mark.parametrize("gt_path", GROUND_TRUTHS, ids=lambda p: p.stem)
def test_non_bnm_doc_meets_acceptance_bar(gt_path, index):
    gt = json.loads(gt_path.read_text(encoding="utf-8"))
    doc_anchors = [a for a in index if a["document_id"] == gt["document_id"]]
    labels = {a["anchor_label"] for a in doc_anchors}

    # (1) Coverage: representative locators are present.
    present = [loc for loc in gt["top_level_locators"] if loc in labels]
    coverage = len(present) / len(gt["top_level_locators"])
    assert coverage >= gt["coverage_floor"], (
        f"{gt['document_id']} coverage {coverage:.0%} < floor "
        f"{gt['coverage_floor']:.0%}; missing {set(gt['top_level_locators']) - labels}")

    # (2) Citable label: every label matches the locator pattern; none is garbage.
    label_re = re.compile(gt["label_pattern"])
    garbage_re = re.compile(gt["garbage_pattern"])
    for a in doc_anchors:
        assert label_re.search(a["anchor_label"]), (
            f"label {a['anchor_label']!r} does not match {gt['label_pattern']!r}")
        assert not garbage_re.search(a["anchor_label"]), (
            f"label {a['anchor_label']!r} matches garbage pattern")

    # (3) Verbatim is enforced at build time by verify_substring; re-assert the
    # anchor carries non-empty text.
    for a in doc_anchors:
        assert a["text"].strip()
```

- [ ] **Step 3: Produce the committed anchor-index.json (live, opt-in)**

Run the live build for the target non-BNM doc(s) plus the BNM corpus, using Azure DI + the boundary model, then commit the artifact. This is a deliberate, reviewed act (per the determinism boundary):

```bash
PYTHONPATH=. .venv/bin/python -c "from engine.build import build_anchor_index; from engine.config import DOCUMENTS; build_anchor_index(DOCUMENTS, output_dir=__import__('pathlib').Path('data/artifacts'))"
```

Then inspect coverage and set `coverage_floor` in the fixture to the measured value (rounded down). If the built label set for a doc shows garbage, fix the prompt (Task 3) and rebuild before committing.

- [ ] **Step 4: Run the acceptance test to verify it passes**

Run: `.venv/bin/python -m pytest engine/tests/test_anchor_coverage.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engine/tests/test_anchor_coverage.py engine/tests/fixtures/ground_truth/ data/artifacts/anchor-index.json
git commit -m "test(engine): anchor coverage/verbatim/citable acceptance harness"
```

---

### Task 9: Full-suite regression gate

Confirm the whole engine suite is green — especially the BNM citation-integrity guards — after the migration.

**Files:** none (verification task).

- [ ] **Step 1: Run the full engine suite**

Run: `.venv/bin/python -m pytest engine/tests/ -q`
Expected: PASS — all tests including `test_artifact_integrity.py`, `test_taxonomy_traces.py`, `test_connections.py`, and the new anchor tests.

- [ ] **Step 2: Confirm no BNM trace orphaned**

Run: `.venv/bin/python -m pytest engine/tests/test_artifact_integrity.py::test_all_committed_traces_still_resolve -v`
Expected: PASS (both committed traces resolve; BNM anchor_ids unchanged).

- [ ] **Step 3: Commit (if any fixups were needed)**

```bash
git add -A engine/
git commit -m "test(engine): green full suite after AnchorIndex migration"
```
