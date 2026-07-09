"""Clause parser (anchor-slice) + ClauseIndex — verbatim clause fetch by number.

Design (see docs/specs/rulebook-radar/spec-knowledge-graph-engine.md,
"Clause parsing (stage 2)"): an LLM finds clause *boundaries* only — it never
produces clause text. It returns, in document order, one record per clause:
``{clause_number, starts_with, heading, parent}`` where ``starts_with`` is a
short verbatim opening phrase. Code then:

1. locates each anchor by string-searching ``starts_with`` in the raw
   markdown (a real, code-verified character position);
2. slices each clause's ``text`` as the span from its anchor to the next
   clause's anchor, in document order — a literal substring of the source,
   byte-for-byte verbatim by construction.

Failure modes (unfound/ambiguous anchor, incomplete clause set) are loud
exceptions raised at build time — never silent corruption.
"""

import logging
import re
from typing import NotRequired, Optional, TypedDict, cast


logger = logging.getLogger(__name__)

# Canonical clause numbers are "{PolicyShortName} {number}" — matching how the
# corpus labels clauses and how the spec's Acceptance Criteria quote them.
POLICY_SHORT_NAMES = {
    "rmit": "RMiT",
    "outsourcing": "Outsourcing",
    "bcm": "BCM",
    "opres": "Operational Resilience",
    "recovery-planning": "Recovery Planning",
    "customer-info": "Customer Info",
    # External references (#26) — each contributes a single hand-anchored passage
    # clause (e.g. "PDPA 129"); kept distinct from the internal cluster policies.
    "mas-trm": "MAS TRM",
    "pdpa": "PDPA",
    "basel-por": "Basel POR",
}


class ClauseEntry(TypedDict):
    clause_number: str
    policy_id: str
    document_id: str
    text: str
    heading: Optional[str]
    source: str
    parent: Optional[str]
    children: list[str]
    superseded_versions: list[str]
    # Internal-only (leading `_`): the composed source span for a parent
    # clause, used by `ClauseIndex.full_text`. Never part of the public
    # clause-index contract; absent on leaf/sub-item entries.
    _full_text: NotRequired[str]


class ClauseAnchorNotFoundError(Exception):
    """Raised when an anchor's `starts_with` snippet is absent from the markdown."""


class ClauseAnchorAmbiguousError(Exception):
    """Raised when an anchor's `starts_with` snippet matches more than once."""


class ClauseCompletenessError(Exception):
    """Raised when the emitted clause set does not cover the expected clauses."""


class ClauseVersionNotFoundError(Exception):
    """Raised when a clause_number is known but the requested version is not.

    Distinct from an unknown `clause_number` (which `ClauseIndex.get` reports
    as `None`) so the API layer (#6 Task 6) can tell `404 CLAUSE_NOT_FOUND`
    apart from `404 CLAUSE_VERSION_NOT_FOUND`.
    """


class ClausePrimaryIndexCollisionError(Exception):
    """Raised when two documents at equal precedence both claim the primary
    (current) slot for the same clause_number — an ambiguous collision that
    must never be silently resolved by picking one."""


def _short_name(policy_id: str) -> str:
    try:
        return POLICY_SHORT_NAMES[policy_id]
    except KeyError as exc:
        raise KeyError(
            f"No policy short-name mapping for policy_id '{policy_id}' — "
            f"add it to POLICY_SHORT_NAMES in engine/clauses.py"
        ) from exc


def _canonical(policy_id: str, bare_number: str) -> str:
    return f"{_short_name(policy_id)} {bare_number}"


def _in_text_label(bare_number: str) -> str:
    """The literal label that appears in the markdown immediately before a
    clause's opening text, given its bare clause number.

    `starts_with` anchors are pure content (no leading label — see the
    module docstring), so the raw span between two anchors includes the
    *next* clause's label bleeding onto the end of the *current* clause's
    text (e.g. "...arrangement.\\n\\n12.2 "). This is what gets trimmed off,
    and the label is also used to disambiguate a recurring anchor phrase.

    The visible label is the clause's **deepest** parenthetical group — the one
    that actually appears immediately before its text in the source. For a
    single-level sub-item ("17.1(a)") that is "(a)"; for a multi-level nesting
    ("9.6(c)(i)") it is only the last group "(i)", NOT "(c)(i)". A top-level
    number ("17.2", "10.50") or non-numeric clause ("Appendix 10") has no
    parenthetical part, so the label is the literal string itself.
    """
    groups = re.findall(r"\([^()]*\)", bare_number)
    if groups:
        return groups[-1]
    return bare_number


# BNM clauses are each preceded by a lone "S" (Standard) or "G" (Guidance)
# marker on its own line. When slicing a clause up to the *next* clause's
# anchor, that next clause's marker leaks onto the tail of the current clause's
# text (e.g. "...arrangement.\n\nS\n\n12.2\n"). This matches a trailing marker.
_TRAILING_MARKER_RE = re.compile(r"\s[SG]\s*$")


def _trim_trailing_label(
    markdown: str, end: int, next_bare_number: Optional[str]
) -> int:
    """Adjust a clause's slice end-point to exclude the next clause's label,
    its BNM Standard/Guidance marker, and separator whitespace.

    `starts_with` anchors quote content only, never the numbering label (see
    module docstring), so a raw slice up to the next clause's anchor position
    picks up that next clause's leading scaffolding bleeding onto the end of the
    current clause's text. In the real corpus that scaffolding is, in order from
    the current clause's real end: whitespace, an optional lone "S"/"G" marker
    line, whitespace, the next clause's label, whitespace. This strips all of
    it, returning the true end of the current clause's own content.
    """
    if next_bare_number is None:
        return end

    label = _in_text_label(next_bare_number)

    # 1. Walk back past trailing whitespace, then the next clause's label if it
    #    sits immediately before `end` (allowing whitespace between).
    j = end
    while j > 0 and markdown[j - 1] in " \n\t\r":
        j -= 1
    label_start = j - len(label)
    if label_start >= 0 and markdown[label_start:j] == label:
        end = label_start
    else:
        # Label not where expected — leave `end` as the raw boundary but still
        # trim trailing whitespace/marker below.
        end = j if j < end else end

    # 2. Trim trailing whitespace, then a lone "S"/"G" marker if present, then
    #    any further whitespace — the next clause's Standard/Guidance indicator.
    while end > 0 and markdown[end - 1] in " \n\t\r":
        end -= 1
    marker = _TRAILING_MARKER_RE.search(markdown, 0, end)
    if marker and marker.end() == end:
        end = marker.start()
        while end > 0 and markdown[end - 1] in " \n\t\r":
            end -= 1
    return end


def _find_anchor_positions(markdown: str, snippet: str) -> list[int]:
    """Return the start offsets in `markdown` where `snippet` occurs,
    whitespace-insensitively.

    The parser LLM quotes a verbatim opening phrase, but MarkItDown's PDF output
    contains runs of doubled spaces and mid-sentence newlines (a layout artifact
    — "This  policy  document  must  be  read" appears thousands of times in the
    corpus). The model normalises those to single spaces when it quotes them, so
    an exact `str.find` misses. Matching each whitespace run in the snippet
    against one-or-more whitespace characters in the source recovers the real
    position — and callers slice the raw source from that position, so the
    stored clause `text` stays byte-for-byte verbatim (original spacing intact).

    A snippet with no non-whitespace content matches nothing (returns []).
    """
    tokens = snippet.split()
    if not tokens:
        return []
    pattern = re.compile(r"\s+".join(re.escape(token) for token in tokens))
    return [match.start() for match in pattern.finditer(markdown)]


def _preceded_by_label(markdown: str, position: int, label: str) -> bool:
    """True if `label` sits immediately before `position` in `markdown`, allowing
    whitespace between the label and the position.

    Used to disambiguate a `starts_with` phrase that occurs more than once: the
    real clause start is preceded by the clause's own label (e.g. "(c)" for a
    sub-item, "8.4" for a top-level clause), whereas an incidental repeat of the
    phrase inside another clause is not. Walks back past whitespace, then checks
    the preceding characters equal `label`.
    """
    i = position
    while i > 0 and markdown[i - 1] in " \n\t\r":
        i -= 1
    start = i - len(label)
    return start >= 0 and markdown[start:i] == label


def _record_drop(
    dropped_report: Optional[list[dict]],
    document_id: str,
    anchor: dict,
    reason: str,
) -> None:
    """Append one dropped-anchor record to `dropped_report` if a report list was
    supplied (the "flag for human review" surface). No-op when `None`, so the
    warn-only default path is unchanged. Captures the anchor's `heading` and
    `starts_with` alongside the reason so a reviewer can locate the clause in the
    source without re-running the parser."""
    if dropped_report is None:
        return
    dropped_report.append(
        {
            "document_id": document_id,
            "clause_number": anchor.get("clause_number"),
            "reason": reason,
            "heading": anchor.get("heading"),
            "starts_with": anchor.get("starts_with"),
        }
    )


def build_clause_index(
    anchors: list[dict],
    markdown: str,
    document_id: str,
    policy_id: str,
    source: str,
    expected_clauses: Optional[set[str]] = None,
    dropped_report: Optional[list[dict]] = None,
) -> dict[str, ClauseEntry]:
    """Locate anchors, slice verbatim text, and build one document's clause entries.

    `anchors` is a list of ``{clause_number, starts_with, heading, parent}``
    records in document order (the LLM's emitted structure — see module
    docstring). `clause_number` and `parent` are *bare* numbers (e.g. "17.1",
    "17.1(a)") as they appear in the source; this function canonicalises them
    to "{PolicyShortName} {number}" for the returned keys.

    Returns a dict keyed by canonical clause_number -> ClauseEntry, for this
    document only (`superseded_versions` is left empty here — populated by
    `merge_clause_indexes` across documents).

    Unresolvable anchors (empty / not-found / ambiguous `starts_with`) are
    DROPPED with a logged warning and a per-document summary, not raised — the
    real BNM corpus has a long tail of deeply-nested boilerplate sub-items the
    LLM cannot anchor uniquely, and crashing on each defeats the build. The
    `ClauseCompletenessError` reconcile is the backstop for *required* clauses.

    `dropped_report`, when supplied, is appended to (never replaced) with one
    ``{document_id, clause_number, reason}`` record per dropped anchor — the
    "flag for human review" surface, so a dropped clause becomes a reviewable
    artifact (`data/artifacts/dropped-clauses.json`) rather than a log line that
    scrolls away. `reason` is one of ``empty_starts_with`` / ``not_found`` /
    ``ambiguous``. Passing ``None`` keeps the old behaviour (warn-only).

    Raises:
        ClauseCompletenessError: `expected_clauses` is supplied and the
            emitted canonical clause set does not cover it (a *load-bearing*
            clause was dropped or never parsed).
    """
    # Resolve each anchor to a single source position, DROPPING (not crashing on)
    # any anchor we cannot place unambiguously. Three drop reasons, all logged
    # loudly and counted, all rooted in imperfect PDF extraction / LLM anchors:
    #
    #   1. empty `starts_with` — the parser saw a clause number but had no
    #      quotable text (a clause body separated from its number in
    #      conversion, e.g. Outsourcing 8.2/8.3);
    #   2. not found — the quoted phrase isn't in the markdown (paraphrased or
    #      from a garbled region);
    #   3. ambiguous — the phrase recurs and the clause's own label can't single
    #      one occurrence out (boilerplate sub-item phrasing, or a label variant
    #      like "iii)" vs "(iii)").
    #
    # Dropping keeps the build converging on real BNM PDFs (deeply-nested
    # boilerplate sub-items are the overwhelming majority of drops, not
    # load-bearing clauses). The `expected_clauses` completeness reconcile is
    # the backstop that still fails the build if a *required* clause is dropped.
    resolved_anchors: list[dict] = []
    positions: list[int] = []
    dropped: list[str] = []

    for anchor in anchors:
        snippet = anchor["starts_with"]
        if not snippet.strip():
            dropped.append(anchor["clause_number"])
            _record_drop(dropped_report, document_id, anchor, "empty_starts_with")
            logger.warning(
                "Dropping clause '%s' in '%s': empty starts_with "
                "(clause text not recoverable from the converted markdown)",
                anchor["clause_number"],
                document_id,
            )
            continue

        occurrences = _find_anchor_positions(markdown, snippet)
        if len(occurrences) == 0:
            dropped.append(anchor["clause_number"])
            _record_drop(dropped_report, document_id, anchor, "not_found")
            logger.warning(
                "Dropping clause '%s' in '%s': starts_with %r not found "
                "(paraphrased or from a garbled region)",
                anchor["clause_number"],
                document_id,
                snippet,
            )
            continue

        if len(occurrences) > 1:
            # A phrase can recur (a clause quoted elsewhere, or boilerplate
            # sub-item text). The real start is the occurrence preceded by this
            # clause's own label ("(c)" for "8.4(c)", "(iii)" for "9.6(c)(iii)",
            # "8.4" for a top-level clause). Use it iff it singles out exactly
            # one; otherwise the anchor is unresolvable — drop it.
            label = _in_text_label(anchor["clause_number"])
            labelled = [
                p for p in occurrences if _preceded_by_label(markdown, p, label)
            ]
            if len(labelled) == 1:
                resolved_anchors.append(anchor)
                positions.append(labelled[0])
                continue
            dropped.append(anchor["clause_number"])
            _record_drop(dropped_report, document_id, anchor, "ambiguous")
            logger.warning(
                "Dropping clause '%s' in '%s': starts_with %r is ambiguous "
                "(found %d times, label %r matched %d)",
                anchor["clause_number"],
                document_id,
                snippet,
                len(occurrences),
                label,
                len(labelled),
            )
            continue

        resolved_anchors.append(anchor)
        positions.append(occurrences[0])

    if dropped:
        logger.warning(
            "Document '%s': dropped %d of %d anchors (%s)",
            document_id,
            len(dropped),
            len(anchors),
            ", ".join(dropped),
        )

    return _assemble_entries(
        anchors=resolved_anchors,
        positions=positions,
        markdown=markdown,
        document_id=document_id,
        policy_id=policy_id,
        source=source,
        expected_clauses=expected_clauses,
        dropped_report=dropped_report,
    )


def _assemble_entries(
    anchors: list[dict],
    positions: list[int],
    markdown: str,
    document_id: str,
    policy_id: str,
    source: str,
    expected_clauses: Optional[set[str]],
    dropped_report: Optional[list[dict]],
    raw_ends: Optional[list[int]] = None,
) -> dict[str, ClauseEntry]:
    """Slice verbatim clause text between consecutive anchor positions and build
    the per-document clause entries. Shared by both the phrase-locating
    `build_clause_index` and the deterministic `segment_clauses` — everything
    downstream of "we know each clause's start offset" lives here.

    `anchors[i]` starts at `positions[i]` (a real offset in `markdown`); each
    clause's `text` is the byte-for-byte slice up to its raw end, with the next
    clause's leading label + S/G marker trimmed. `parent` is taken from the
    anchor (each caller supplies it — the LLM path from the model, the segmenter
    from structural derivation).

    `raw_ends`, when supplied (the segmenter path), gives each clause's raw end
    offset explicitly — needed because a clause can be terminated by a *section
    heading* ("9 Governance"), not only by the next clause, and the heading must
    not bleed into the clause's text. When ``None`` (the phrase-locator path) the
    raw end is the next anchor's position, exactly as before — so that path is
    byte-for-byte unchanged.

    A child whose parent is not itself an emitted clause is promoted to
    top-level and flagged, never crashed on (KeyError).
    """
    entries: dict[str, ClauseEntry] = {}
    children_by_parent: dict[str, list[str]] = {}
    raw_start_by_clause: dict[str, int] = {}
    trimmed_end_by_clause: dict[str, int] = {}

    for i, anchor in enumerate(anchors):
        start = positions[i]
        if raw_ends is not None:
            raw_end = raw_ends[i]
        else:
            raw_end = positions[i + 1] if i + 1 < len(anchors) else len(markdown)
        next_bare_number = (
            anchors[i + 1]["clause_number"] if i + 1 < len(anchors) else None
        )
        end = _trim_trailing_label(markdown, raw_end, next_bare_number)
        text = markdown[start:end]

        clause_number = _canonical(policy_id, anchor["clause_number"])
        parent_bare = anchor.get("parent")
        parent = _canonical(policy_id, parent_bare) if parent_bare else None

        entries[clause_number] = {
            "clause_number": clause_number,
            "policy_id": policy_id,
            "document_id": document_id,
            "text": text,
            "heading": anchor.get("heading"),
            "source": source,
            "parent": parent,
            "children": [],
            "superseded_versions": [],
        }
        raw_start_by_clause[clause_number] = start
        # Store the *trimmed* end (label + S/G marker stripped), so the composed
        # parent full_text ends as cleanly as each child's own text does.
        trimmed_end_by_clause[clause_number] = end

        if parent:
            children_by_parent.setdefault(parent, []).append(clause_number)

    for parent, children in children_by_parent.items():
        if parent not in entries:
            # The child's parent is not itself an emitted clause — a bare section
            # heading (e.g. "10 Cloud services") or a parent whose anchor was
            # dropped. Rather than KeyError-crash the build, PROMOTE the orphaned
            # children to top-level (parent -> None) and FLAG each for review.
            for child in children:
                entries[child]["parent"] = None
                _record_drop(
                    dropped_report,
                    document_id,
                    {
                        "clause_number": entries[child]["clause_number"],
                        "heading": entries[child]["heading"],
                        "starts_with": None,
                    },
                    f"orphaned_parent:{parent}",
                )
            logger.warning(
                "Document '%s': parent clause '%s' missing for %d child(ren) "
                "(%s) — promoting them to top-level and flagging for review",
                document_id,
                parent,
                len(children),
                ", ".join(children),
            )
            continue
        entries[parent]["children"] = children
        # Composed view (Option C): the contiguous source span covering the
        # parent's stem plus all its children, in document order — a real
        # substring of `markdown` (including the children's numbering
        # labels/whitespace that individual `text` fields exclude).
        # Assembled once here from the anchor positions, not stored as part
        # of the public clause-index contract (private key, leading `_`).
        last_child = children[-1]
        span_start = raw_start_by_clause[parent]
        span_end = trimmed_end_by_clause[last_child]
        entries[parent]["_full_text"] = markdown[span_start:span_end]

    if expected_clauses:
        missing = expected_clauses - set(entries.keys())
        if missing:
            raise ClauseCompletenessError(
                f"Document '{document_id}' is missing expected clauses: "
                f"{sorted(missing)}"
            )

    return entries


def merge_clause_indexes(
    document_entries: list[tuple[str, dict[str, ClauseEntry]]],
    current_document_id: str,
) -> tuple[dict[str, ClauseEntry], dict[str, dict[str, ClauseEntry]]]:
    """Merge several documents' per-document clause entries into the final
    keyed primary index, applying the version-keying rule: the entry from
    `current_document_id` wins the primary-index slot for any clause_number
    it defines; entries from other documents for the same clause_number are
    recorded in the winner's `superseded_versions` and kept reachable via the
    returned `versions` map (for `ClauseIndex.get(..., version=document_id)`).

    A clause_number that exists in only one document (no version conflict)
    is simply carried through to the primary index as-is, `superseded_versions`
    left empty.

    Build invariant: exactly one entry lands in the primary index per
    clause_number. If two *non-current* documents both define the same
    clause_number (an ambiguous collision at equal, non-current precedence),
    this raises `ClausePrimaryIndexCollisionError` rather than silently
    picking one — this should not happen for the locked demo cluster (each
    policy_id has at most one non-current version) but is guarded regardless.

    Returns `(primary, versions)`:
    - `primary`: canonical clause_number -> current ClauseEntry.
    - `versions`: canonical clause_number -> {document_id -> ClauseEntry},
      every version of that clause across all supplied documents.
    """
    versions: dict[str, dict[str, ClauseEntry]] = {}
    for document_id, entries in document_entries:
        for clause_number, entry in entries.items():
            versions.setdefault(clause_number, {})[document_id] = entry

    primary: dict[str, ClauseEntry] = {}
    for clause_number, by_document in versions.items():
        if current_document_id in by_document:
            winner_document_id = current_document_id
        else:
            other_document_ids = list(by_document.keys())
            if len(other_document_ids) > 1:
                raise ClausePrimaryIndexCollisionError(
                    f"Clause '{clause_number}' has {len(other_document_ids)} "
                    f"non-current versions ({sorted(other_document_ids)}) and "
                    f"none is the current document "
                    f"'{current_document_id}' — ambiguous primary-index "
                    f"collision, refusing to pick one"
                )
            winner_document_id = other_document_ids[0]

        winner_entry = cast(ClauseEntry, dict(by_document[winner_document_id]))
        superseded = sorted(
            doc_id for doc_id in by_document if doc_id != winner_document_id
        )
        winner_entry["superseded_versions"] = superseded
        primary[clause_number] = winner_entry

    return primary, versions


def build_reference_clause(
    document_id: str,
    policy_id: str,
    anchor: str,
    heading: Optional[str],
    text: str,
    source: str = "reference",
) -> dict[str, ClauseEntry]:
    """Build the single verbatim passage clause for an external reference (#26).

    External references (MAS TRM, PDPA, Basel POR) are not BNM-numbered, so the
    deterministic `segment_clauses` grammar does not apply. Each public reference
    instead contributes exactly ONE clause, keyed by the canonical
    "{PolicyShortName} {anchor}" (e.g. ``"PDPA 129"``), whose ``text`` is the
    exact verbatim excerpt from the real source (see
    ``engine.config.REFERENCE_DOCUMENTS``). Restricted/preview references have no
    passage and never call this.

    Returns a one-entry dict shaped exactly like a `build_clause_index` /
    `segment_clauses` result, so `merge_clause_indexes`, `ClauseIndex`, the API,
    and the graph treat a reference clause identically to a policy clause.
    """
    clause_number = _canonical(policy_id, anchor)
    entry: ClauseEntry = {
        "clause_number": clause_number,
        "policy_id": policy_id,
        "document_id": document_id,
        "text": text,
        "heading": heading,
        "source": source,
        "parent": None,
        "children": [],
        "superseded_versions": [],
    }
    return {clause_number: entry}


class ClauseIndex:
    """Read-only, verbatim clause lookup.

    Wraps the *primary* index (current version per clause_number — see the
    version-keying rule in the spec's Data Model section) plus, optionally, a
    full version map for historical `?version=` lookups.
    """

    def __init__(
        self,
        primary: dict[str, ClauseEntry],
        versions: Optional[dict[str, dict[str, ClauseEntry]]] = None,
    ) -> None:
        self._primary = primary
        if versions is not None:
            self._versions = versions
        else:
            # No explicit version map supplied — fall back to each primary
            # entry being the only known version of itself.
            self._versions = {
                clause_number: {entry["document_id"]: entry}
                for clause_number, entry in primary.items()
            }

    def get(
        self, clause_number: str, version: Optional[str] = None
    ) -> Optional[ClauseEntry]:
        """Fetch a clause entry verbatim.

        - `version=None` (default): the current/primary entry, or `None` if
          `clause_number` is not in the corpus at all.
        - `version=<document_id>`: a specific historical version. Returns
          `None` if `clause_number` itself is unknown; raises
          `ClauseVersionNotFoundError` if `clause_number` is known but has
          no entry under that `document_id`.
        """
        if version is None:
            return self._primary.get(clause_number)

        versions_for_clause = self._versions.get(clause_number)
        if versions_for_clause is None:
            return None
        if version not in versions_for_clause:
            raise ClauseVersionNotFoundError(
                f"No version '{version}' for clause '{clause_number}'"
            )
        return versions_for_clause[version]

    def entries_for_document(self, document_id: str) -> list[ClauseEntry]:
        """Return every primary clause entry belonging to `document_id`, in
        insertion (document) order.

        A read-only accessor for callers that need a whole document's clause
        text at once (e.g. the finder/critic connection agents, which build a
        per-document clause-context block). Only the primary/current entries
        are returned — historical `?version=` entries are not included. An
        unknown `document_id` yields an empty list.
        """
        return [
            entry
            for entry in self._primary.values()
            if entry["document_id"] == document_id
        ]

    def full_text(
        self, clause_number: str, version: Optional[str] = None
    ) -> Optional[str]:
        """Composed view for a parent clause: stem text + all children's text,
        concatenated in document order (assembled on demand, not stored).

        This is a contiguous substring of the source markdown (it includes
        the children's numbering labels/whitespace, unlike each child's own
        `text`) and starts with the stem. For a leaf/sub-item (no children)
        this is identical to its own `text`. Returns `None` if
        `clause_number` is unknown.
        """
        entry = self.get(clause_number, version=version)
        if entry is None:
            return None

        if not entry["children"]:
            return entry["text"]
        return entry["_full_text"]


# Matches a BNM top-level section heading on its own line: a bare number
# ("12", "17") or "Appendix N", followed by a space and a title. Anchored to
# line start; the `re.MULTILINE` flag makes `^` match at each line.
# Lines that are page-header/footer or table-of-contents noise in the real
# MarkItDown output of BNM PDFs (validated against the demo corpus), not clause
# content. Stripped before chunking so the parser LLM never sees them.
# - dotted leaders ("......") are table-of-contents entries;
# - "Issued on: <date>" is the running page header repeated on every page;
# - "<N> of <M>" is the page-number footer;
# - a lone "PART A"/"PART B" marker is a structural divider, not a clause.
_TOC_LEADER_RE = re.compile(r"\.{4,}")
_NOISE_LINE_RES = [
    re.compile(r"^\s*Issued on:.*$"),
    re.compile(r"^\s*\d+\s+of\s+\d+\s*$"),
    re.compile(r"^\s*PART\s+[A-Z]\b.*$"),
]

# ---------------------------------------------------------------------------
# Deterministic clause segmentation (rule-primary; supersedes the LLM parser).
#
# BNM policy documents have a REGULAR line-start grammar once ingested cleanly
# (Azure Document Intelligence fixes the reading-order scramble). Rather than
# ask an LLM to quote an anchor phrase and then re-locate it — the round-trip
# that produced not-found / ambiguous / empty / non-JSON / non-deterministic
# failures — `segment_clauses` finds every clause boundary directly with these
# anchored regexes, derives the hierarchy from the numbers themselves, and slices
# verbatim text between boundaries. Fully deterministic (same bytes every run,
# so artifacts freeze cleanly) and network-free.
#
# The grammar, each anchored at line start (MULTILINE):
#   - a numbered clause:   "8.1 ...", "10.50 ..." (N.M, decimals, any depth)
#   - a lettered sub-item: "(a) ...", "(b) ...", "(i) ..." — belongs to the
#     nearest preceding numbered clause; parent derived structurally
#   - an appendix clause:  "Appendix 7"
#   - a SECTION HEADING:   "8 Governance" (bare N + Title) — NOT a clause; it
#     sets the `heading` for the clauses that follow and bounds the previous
#     clause's text. Distinguished from a footnote ("44 This is also...") by
#     sequence: headings form the low monotonic run 1..N of the document's parts.
# The clause-number label may be followed by its text on the SAME line
# ("6.1 This policy...") OR stand ALONE on its own line ("12.1\nA financial...")
# — the real BNM+Document-Intelligence output uses both forms, so the trailing
# `(?:\s|$)` accepts either. A bare-label line's actual content is then picked up
# from the following line(s) via `_skip_ws` (which skips newlines) + the
# continuation-line accumulation in the main loop.
_NUMBERED_CLAUSE_RE = re.compile(r"^(\d+(?:\.\d+)+)(?:\s|$)")
_SUBITEM_RE = re.compile(r"^\(([a-z]{1,3}|[ivxl]{1,4})\)(?:\s|$)")
_APPENDIX_RE = re.compile(r"^(Appendix\s+\d+)\b")
_SECTION_HEADING_RE = re.compile(r"^(\d+)\s+([A-Z].*)$")


class _Boundary(TypedDict):
    line_start: int  # offset of the line in the markdown
    content_start: int  # offset where the clause's OWN text begins (after label)
    content_end: int  # offset where the clause's own text ends (before next
    # boundary / any intervening non-clause lines like a section heading)
    bare_number: str  # e.g. "8.1", "8.1(a)", "Appendix 7"
    parent: Optional[str]  # bare number of structural parent, or None
    heading: Optional[str]  # enclosing section heading at this point


# Structural divider lines that sit between clauses in BNM documents (e.g.
# "PART B", "POLICY REQUIREMENTS", "OVERVIEW"). They are NOT clauses and must not
# bleed into the preceding clause's text, but — unlike page/TOC noise — we keep
# them in the source string so every clause slice stays byte-for-byte verbatim
# against the ORIGINAL markdown. They are recognised only to end a clause early.
_DIVIDER_LINE_RE = re.compile(r"^(?:PART\s+[A-Z]\b.*|[A-Z][A-Z ]{2,})$")
# A page/TOC noise line (see `_strip_noise`) — recognised inline here so the
# segmenter can skip it as a boundary WITHOUT removing it from the source (which
# would break verbatim-against-source slicing). Note: the "PART X" pattern from
# `_NOISE_LINE_RES` is deliberately EXCLUDED — a "PART B" line is a structural
# DIVIDER that must CLOSE the preceding clause (via `_DIVIDER_LINE_RE`), not be
# silently skipped (which would let the previous clause absorb it).
_INLINE_NOISE_RES = [
    re.compile(r"^\s*Issued on:.*$"),
    re.compile(r"^\s*\d+\s+of\s+\d+\s*$"),
]


def _iter_lines_with_offsets(text: str) -> list[tuple[int, str]]:
    """Yield ``(offset, line)`` for each line in `text`, where `offset` is the
    line's start position in `text`. Line content excludes the trailing newline.
    """
    result: list[tuple[int, str]] = []
    pos = 0
    for line in text.splitlines(keepends=True):
        result.append((pos, line.rstrip("\n")))
        pos += len(line)
    return result


def segment_clauses(
    markdown: str,
    document_id: str,
    policy_id: str,
    source: str,
    expected_clauses: Optional[set[str]] = None,
    dropped_report: Optional[list[dict]] = None,
) -> dict[str, ClauseEntry]:
    """Deterministically segment a document's clean markdown into clause entries.

    The rule-primary replacement for the LLM parser (`find_clause_anchors` +
    `build_clause_index`). Single stateful pass over lines:

    1. Classify each line by anchored regex: a numbered clause (``N.M``…), a
       lettered/roman sub-item (``(a)``, ``(i)``), an appendix (``Appendix N``),
       or a bare section heading (``8 Governance``).
    2. Track the current section heading and the current numbered clause so a
       sub-item's parent is derived *structurally* from the numbers (``8.1(a)``'s
       parent is ``8.1``) — never guessed by a model.
    3. Record each clause's line-start, content-start (after its label), and the
       raw end (the next boundary of any kind, including a section heading).
    4. Hand the boundaries to `_assemble_entries`, which slices verbatim text and
       builds the same `ClauseEntry` dict the LLM path produced — so the artifact
       contract, `ClauseIndex`, API and graph are all unchanged.

    A bare-integer line is a section heading only when its number is the monotonic
    successor of the previous heading (1, 2, 3, …) — this rejects footnotes
    ("44 This is also applicable…"), which are out of sequence, without an LLM.

    Fully deterministic and network-free: same bytes in → same entries out (so
    artifacts freeze cleanly). `expected_clauses` / `dropped_report` behave as in
    `build_clause_index`.

    Segmentation runs over the ORIGINAL `markdown` (offsets true to source), so
    every sliced `text` is byte-for-byte verbatim against the source. Page/TOC
    noise and structural dividers ("PART B", "POLICY REQUIREMENTS") are skipped
    as boundaries but never removed; a clause's text ends at the last line of its
    own content, before any following divider/heading (`content_end`).
    """
    boundaries: list[_Boundary] = []
    current_heading: Optional[str] = None
    current_numbered: Optional[str] = None  # nearest preceding N.M clause
    last_section_number = 0  # for the monotonic-successor heading test
    # Index of the clause whose text is still being accumulated. A continuation
    # line extends it; the FIRST divider/heading/new-clause after it CLOSES it
    # (set to None) so later dividers cannot push its end further (the 7.1-eats-
    # PART-B bug). Only a new clause/sub-item/appendix opens a fresh one.
    open_index: Optional[int] = None

    def _skip_ws(pos: int) -> int:
        # Skip ALL whitespace incl. newlines, so a bare-label line ("12.1" alone)
        # advances content_start to the next line's real text. For an inline
        # label ("6.1 The board…") there is no leading whitespace to skip beyond
        # the single space, so behaviour is unchanged.
        while pos < len(markdown) and markdown[pos] in " \t\r\n":
            pos += 1
        return pos

    def _close_open(end: int) -> None:
        nonlocal open_index
        if open_index is not None and end > boundaries[open_index]["content_end"]:
            boundaries[open_index]["content_end"] = end
        open_index = None

    for offset, line in _iter_lines_with_offsets(markdown):
        stripped = line.strip()
        if not stripped:
            continue

        # Skip page/TOC noise and TOC-leader lines inline (do not treat as a
        # boundary, do not end the current clause on them, and — crucially — do
        # not remove them, so offsets stay true to the source).
        if _TOC_LEADER_RE.search(stripped) or any(
            p.match(line) for p in _INLINE_NOISE_RES
        ):
            continue

        line_end = offset + len(line)

        # 1. Numbered clause: "8.1 ...", "10.50 ...", "8.1.2 ..."
        m = _NUMBERED_CLAUSE_RE.match(stripped)
        if m:
            bare = m.group(1)
            content_start = _skip_ws(offset + line.index(bare) + len(bare))
            # parent is the number with its last ".K" removed, iff that exists
            parent = bare.rsplit(".", 1)[0] if bare.count(".") >= 2 else None
            _close_open(offset)
            boundaries.append(
                {
                    "line_start": offset,
                    "content_start": content_start,
                    # For a bare-label line, content_start jumped past line_end to
                    # the next line; never let content_end precede it.
                    "content_end": max(line_end, content_start),
                    "bare_number": bare,
                    "parent": parent,
                    "heading": current_heading,
                }
            )
            open_index = len(boundaries) - 1
            current_numbered = bare
            continue

        # 2. Lettered / roman sub-item: "(a) ...", "(i) ..." — attaches to the
        #    nearest preceding numbered clause as "{N.M}({letter})".
        m = _SUBITEM_RE.match(stripped)
        if m and current_numbered is not None:
            letter = m.group(1)
            bare = f"{current_numbered}({letter})"
            label = f"({letter})"
            content_start = _skip_ws(offset + line.index(label) + len(label))
            _close_open(offset)
            boundaries.append(
                {
                    "line_start": offset,
                    "content_start": content_start,
                    "content_end": max(line_end, content_start),
                    "bare_number": bare,
                    "parent": current_numbered,
                    "heading": current_heading,
                }
            )
            open_index = len(boundaries) - 1
            continue

        # 3. Appendix clause: "Appendix 7"
        m = _APPENDIX_RE.match(stripped)
        if m:
            bare = m.group(1)
            _close_open(offset)
            boundaries.append(
                {
                    "line_start": offset,
                    "content_start": offset + line.index("Appendix"),
                    "content_end": line_end,
                    "bare_number": bare,
                    "parent": None,
                    "heading": bare,
                }
            )
            open_index = len(boundaries) - 1
            current_heading = bare
            current_numbered = None
            continue

        # 4. Section heading: "8 Governance". Accepted as a real section boundary
        #    when its number is the monotonic SUCCESSOR of the last (…7 → 8) OR a
        #    RESTART to 1 — the body's "1 Introduction" after a table of contents
        #    has already run the counter up to the last section (e.g. 18). The
        #    restart re-syncs the counter on the real body and skips the TOC
        #    deterministically, with no LLM. Any other number (44, 12 out of
        #    sequence) is a footnote / cross-reference, ignored as a boundary.
        #    A heading is NOT a clause; it CLOSES the previous clause so the
        #    heading text never bleeds into it.
        m = _SECTION_HEADING_RE.match(stripped)
        if m:
            number = int(m.group(1))
            is_successor = number == last_section_number + 1
            is_restart = number == 1 and last_section_number >= 1
            if is_successor or is_restart:
                _close_open(offset)
                current_heading = stripped
                current_numbered = None
                last_section_number = number
            else:
                # A footnote or out-of-sequence bare number ("44 This is …") —
                # NOT a heading and NOT a clause, but it must not extend the
                # current clause's text either (it is page-bottom footnote
                # matter). Close the open clause so the footnote line is
                # excluded, without starting a new boundary.
                _close_open(offset)
            continue

        # 5. A structural divider ("PART B", "POLICY REQUIREMENTS") — not a
        #    clause; closes the previous clause so it never absorbs the divider.
        if _DIVIDER_LINE_RE.match(stripped):
            _close_open(offset)
            current_numbered = None
            continue

        # 6. A plain continuation line of the still-open clause — extend its end.
        if open_index is not None:
            boundaries[open_index]["content_end"] = line_end

    if not boundaries:
        return {}

    # Build the parallel arrays _assemble_entries consumes. Each clause's raw end
    # is its own recorded content_end (the last line of its content, before any
    # divider/heading), which _assemble_entries then right-trims of the next
    # clause's label + S/G marker.
    anchors: list[dict] = [
        {
            "clause_number": b["bare_number"],
            "starts_with": None,
            "heading": b["heading"],
            "parent": b["parent"],
        }
        for b in boundaries
    ]
    positions = [b["content_start"] for b in boundaries]
    raw_ends = [b["content_end"] for b in boundaries]

    return _assemble_entries(
        anchors=anchors,
        positions=positions,
        markdown=markdown,
        document_id=document_id,
        policy_id=policy_id,
        source=source,
        expected_clauses=expected_clauses,
        dropped_report=dropped_report,
        raw_ends=raw_ends,
    )
