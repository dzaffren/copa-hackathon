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

from engine.config import PARSER_DEPLOYMENT
from engine.llm import LLMResponseError, call_chat, parse_json_response

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
    text (e.g. "...arrangement.\\n\\n12.2 "). This is what gets trimmed off.
    For nested sub-items (bare number "17.1(a)") the visible label is only
    the parenthetical part ("(a)"); for a top-level number ("17.2",
    "10.50") or a non-numeric clause ("Appendix 10") it's the literal
    string itself.
    """
    if "(" in bare_number and bare_number.endswith(")"):
        return "(" + bare_number.split("(", 1)[1]
    return bare_number


def _trim_trailing_label(
    markdown: str, end: int, next_bare_number: Optional[str]
) -> int:
    """Adjust a clause's slice end-point to exclude the next clause's label.

    `starts_with` anchors quote content only, never the numbering label
    (see module docstring), so a raw slice up to the next clause's anchor
    position picks up that next clause's label + separator whitespace
    bleeding onto the end of the current clause's text (e.g.
    "...having first:\\n(a) "). This walks back from `end`, past the
    optional single separator space and the label itself (if present
    immediately before `end`), then past any further whitespace/newlines —
    returning the true end of the current clause's own content.
    """
    if next_bare_number is None:
        return end

    label = _in_text_label(next_bare_number)
    j = end
    while j > 0 and markdown[j - 1] == " ":
        j -= 1
    label_start = j - len(label)
    if label_start >= 0 and markdown[label_start:j] == label:
        end = label_start
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


def build_clause_index(
    anchors: list[dict],
    markdown: str,
    document_id: str,
    policy_id: str,
    source: str,
    expected_clauses: Optional[set[str]] = None,
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

    Raises:
        ClauseAnchorNotFoundError: an anchor's `starts_with` is not present
            in `markdown`.
        ClauseAnchorAmbiguousError: an anchor's `starts_with` matches more
            than one position in `markdown`.
        ClauseCompletenessError: `expected_clauses` is supplied and the
            emitted canonical clause set does not cover it.
    """
    positions: list[int] = []
    for anchor in anchors:
        snippet = anchor["starts_with"]
        occurrences = _find_anchor_positions(markdown, snippet)
        if len(occurrences) == 0:
            raise ClauseAnchorNotFoundError(
                f"Anchor for clause '{anchor['clause_number']}' "
                f"(starts_with={snippet!r}) not found in document "
                f"'{document_id}'"
            )
        if len(occurrences) > 1:
            # A phrase can recur (e.g. a clause quoted mid-sentence elsewhere).
            # The real clause start is the occurrence immediately preceded by
            # this clause's own label ("(c)" for "8.4(c)", "8.4" for a
            # top-level clause). Prefer it; only fail if the label can't
            # single out one occurrence.
            label = _in_text_label(anchor["clause_number"])
            labelled = [p for p in occurrences if _preceded_by_label(markdown, p, label)]
            if len(labelled) == 1:
                positions.append(labelled[0])
                continue
            raise ClauseAnchorAmbiguousError(
                f"Anchor for clause '{anchor['clause_number']}' "
                f"(starts_with={snippet!r}) is ambiguous — found "
                f"{len(occurrences)} times in document '{document_id}'"
                f"{f' and the label {label!r} matched {len(labelled)} of them' if labelled else ''}"
            )
        positions.append(occurrences[0])

    entries: dict[str, ClauseEntry] = {}
    children_by_parent: dict[str, list[str]] = {}
    raw_start_by_clause: dict[str, int] = {}
    raw_end_by_clause: dict[str, int] = {}

    for i, anchor in enumerate(anchors):
        start = positions[i]
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
        raw_end_by_clause[clause_number] = raw_end

        if parent:
            children_by_parent.setdefault(parent, []).append(clause_number)

    for parent, children in children_by_parent.items():
        entries[parent]["children"] = children
        # Composed view (Option C): the contiguous source span covering the
        # parent's stem plus all its children, in document order — a real
        # substring of `markdown` (including the children's numbering
        # labels/whitespace that individual `text` fields exclude).
        # Assembled once here from the anchor positions, not stored as part
        # of the public clause-index contract (private key, leading `_`).
        last_child = children[-1]
        span_start = raw_start_by_clause[parent]
        span_end = raw_end_by_clause[last_child]
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

# Chunk size (characters) for splitting a document's body before each parser
# LLM call. Bounds per-call output so the largest docs (RMiT ≈ 204 KB markdown)
# don't risk a truncated response; chunks break on blank lines, never mid-line.
_MAX_CHUNK_CHARS = 6000

PARSER_SYSTEM_PROMPT = """\
You are a parser that finds clause boundaries in a Bank Negara Malaysia (BNM)
policy document. You NEVER produce clause text — only boundary anchors.

BNM clause numbering you must recognise, exactly as it appears in the source:
- top-level decimals: "17.1", "17.2", "12.1"
- deep decimals that are NOT sub-items: "10.50" (distinct from "10.5")
- lettered sub-items: "17.1(a)", "17.1(b)"
- deeper sub-items: "12.3(e)"
- non-numeric clauses: "Appendix 10"

Return, IN DOCUMENT ORDER, ONLY a JSON array (no prose, no markdown fence is
required). Each element is an object with EXACTLY these four keys:
- "clause_number": the bare clause number exactly as written in the source
  (e.g. "17.1", "17.1(a)", "10.50", "Appendix 10"). Do NOT add the policy name.
- "starts_with": a SHORT opening phrase of the clause's OWN text, quoted
  VERBATIM from the source — copied character-for-character, long enough to be
  unique within the document. NEVER the full clause text, NEVER paraphrased,
  NEVER a character offset, and NEVER the leading clause-number label.
- "heading": the enclosing section heading (e.g. "17 Cloud services").
- "parent": the bare clause number of the parent clause (e.g. "17.1" for
  "17.1(a)"), or null for a top-level clause.

Example element:
{"clause_number": "17.1(a)", "starts_with": "completed the risk assessment",
 "heading": "17 Cloud services", "parent": "17.1"}

If this chunk contains NO numbered clauses at all — for example a table of
contents, a cover page, a definitions/interpretation block with no numbered
requirements, or a page fragment — return an empty JSON array: []

CRITICAL OUTPUT RULE: respond with the JSON array and NOTHING else. Your entire
reply must start with the character `[` and end with the character `]`. Do not
write any explanation, preamble, or prose before or after the array — not even
for a chunk with no clauses (return `[]`). Do not echo the source text back.
"""

_REQUIRED_ANCHOR_KEYS = {"clause_number", "starts_with", "heading", "parent"}


def _strip_noise(markdown: str) -> str:
    """Remove table-of-contents and page-header/footer noise from a document's
    MarkItDown output, leaving the clause body.

    Real BNM PDFs convert with repeated running headers ("Issued on: <date>"),
    page-number footers ("3 of 20"), form-feed page breaks, table-of-contents
    entries (dotted leaders "......"), and lone "PART X" dividers — none of
    which are clause content, and all of which confused the parser into
    treating a definitions/TOC page as a clause section (see the demo corpus).
    This drops those lines. Pure and network-free.
    """
    kept: list[str] = []
    for raw_line in markdown.replace("\x0c", "\n").split("\n"):
        line = raw_line.rstrip()
        if _TOC_LEADER_RE.search(line):
            continue
        if any(pattern.match(line) for pattern in _NOISE_LINE_RES):
            continue
        kept.append(line)
    return "\n".join(kept)


# A line that begins a new top-level clause or section — the boundaries a chunk
# is allowed to START on, so a chunk never opens mid-clause (a headless fragment
# confuses the parser LLM into echoing text instead of emitting JSON). Matches a
# decimal clause number ("12.1", "10.50"), a section heading ("12 Approval…"),
# or an appendix ("Appendix 4"). Sub-item labels ("(a)", "(f)") are deliberately
# NOT boundaries — they stay inside their parent clause. The decimal-clause form
# is the reliable signal (the demo corpus's N.M numbering is in-order and
# ungarbled); heading/appendix forms are a bonus. Anchored per-line (MULTILINE).
_CLAUSE_START_RE = re.compile(
    r"^(?:\d+\.\d+\b|\d+\s+[A-Z]|Appendix\s+\d+\b)",
    re.MULTILINE,
)


def _split_chunks(markdown: str, max_chars: int = _MAX_CHUNK_CHARS) -> list[str]:
    """Split a document into clause-aware, size-bounded chunks for per-call LLM
    parsing.

    Strips page/TOC noise (`_strip_noise`), then cuts the body at **top-level
    clause boundaries** (`_CLAUSE_START_RE`) so every chunk BEGINS at a real
    clause or heading — never mid-clause. Consecutive clause blocks are packed
    together up to ``max_chars``; a single clause larger than ``max_chars``
    becomes its own chunk (a clause is never split across calls). This fixes the
    headless-fragment failure that size-only chunking caused, where a chunk
    starting in the middle of a clause made the parser LLM echo source text
    instead of returning JSON. Pure and network-free.

    Falls back to paragraph packing when the document has no detectable clause
    boundaries (so a prose-only document still yields chunks). Returns the
    non-empty chunks in document order (an all-noise document yields an empty
    list).
    """
    body = _strip_noise(markdown).strip()
    if not body:
        return []

    boundaries = [m.start() for m in _CLAUSE_START_RE.finditer(body)]
    if not boundaries:
        return _split_paragraphs(body, max_chars)

    # Blocks = spans between consecutive clause boundaries. Any preamble before
    # the first boundary is kept as a leading block (the parser returns [] for a
    # clause-less block, which is tolerated).
    starts = ([0] + boundaries) if boundaries[0] != 0 else boundaries
    blocks: list[str] = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(body)
        block = body[start:end].strip()
        if block:
            blocks.append(block)

    # Pack whole clause blocks up to max_chars; never split a block.
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for block in blocks:
        addition = len(block) + 2  # +2 for the "\n\n" re-join separator
        if current and current_len + addition > max_chars:
            chunks.append("\n\n".join(current))
            current = []
            current_len = 0
        current.append(block)
        current_len += addition
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def _split_paragraphs(body: str, max_chars: int) -> list[str]:
    """Fallback size-based packing on blank-line-separated paragraphs, for a
    document with no detectable clause boundaries. Never splits mid-line."""
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for paragraph in re.split(r"\n\s*\n", body):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        addition = len(paragraph) + 2
        if current and current_len + addition > max_chars:
            chunks.append("\n\n".join(current))
            current = []
            current_len = 0
        current.append(paragraph)
        current_len += addition
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def _parse_anchor_response(raw: str) -> list[dict]:
    """Parse the parser LLM's raw reply into a validated list of anchor dicts.

    Delegates JSON extraction to `engine.llm.parse_json_response` (handles code
    fences + malformed output), then asserts the result is a list whose every
    element is a dict carrying exactly the four required anchor keys
    (``clause_number``, ``starts_with``, ``heading``, ``parent``). Raises
    `LLMResponseError` if the overall shape is wrong. Pure and network-free.
    """
    parsed = parse_json_response(raw)
    if not isinstance(parsed, list):
        raise LLMResponseError(
            f"Parser LLM must return a JSON array of anchors, got "
            f"{type(parsed).__name__}"
        )

    anchors: list[dict] = []
    for element in parsed:
        if not isinstance(element, dict):
            raise LLMResponseError(
                f"Each anchor must be a JSON object, got "
                f"{type(element).__name__}: {element!r}"
            )
        missing = _REQUIRED_ANCHOR_KEYS - element.keys()
        if missing:
            raise LLMResponseError(
                f"Anchor is missing required key(s) {sorted(missing)}: "
                f"{element!r}"
            )
        anchors.append(element)
    return anchors


def find_clause_anchors(markdown: str, document_id: str) -> list[dict]:
    """Call the parser LLM (Azure AI Foundry, Claude) to find clause anchors.

    Strips page/TOC noise and splits `markdown` into size-bounded chunks
    (`_split_chunks`), calls the parser deployment once per chunk via
    `engine.llm.call_chat` with `PARSER_SYSTEM_PROMPT`, parses each reply with
    `_parse_anchor_response` (a clause-less chunk legitimately yields `[]`), and
    concatenates the per-chunk anchor lists in document order. Returns one
    ``{clause_number, starts_with, heading, parent}`` dict per clause (bare
    numbers, not canonical) — exactly the shape `build_clause_index` consumes.

    This is the network seam — real callers use it; tests never call it for
    real (they stub anchors by hand and call `build_clause_index` directly, or
    monkeypatch `call_chat`). `PARSER_DEPLOYMENT` is the confirmed cheap
    deployment for this mechanical boundary-finding stage (see spec Solution
    Design, "Model access & config").
    """
    chunks = _split_chunks(markdown, _MAX_CHUNK_CHARS)
    anchors: list[dict] = []
    for i, chunk in enumerate(chunks, start=1):
        logger.info("  [%s] parsing chunk %d/%d", document_id, i, len(chunks))
        found = _parse_chunk_with_retry(chunk, document_id, i)
        anchors.extend(found)
        logger.info("  [%s] chunk %d → %d clauses", document_id, i, len(found))
    return anchors


def _parse_chunk_with_retry(
    chunk: str, document_id: str, chunk_index: int, attempts: int = 3
) -> list[dict]:
    """Call the parser LLM for one chunk, retrying on a non-JSON reply.

    Claude occasionally echoes source text instead of emitting JSON (a
    sporadic failure, most often on a confusing chunk). Since it's
    non-deterministic, a re-ask usually succeeds — so call up to ``attempts``
    times, returning the first reply `_parse_anchor_response` accepts. If every
    attempt fails, re-raise the last `LLMResponseError` so the build fails
    loudly (a dropped chunk would mean silently missing clauses).
    """
    last_error: LLMResponseError | None = None
    for attempt in range(1, attempts + 1):
        raw = call_chat(PARSER_DEPLOYMENT, PARSER_SYSTEM_PROMPT, chunk)
        try:
            return _parse_anchor_response(raw)
        except LLMResponseError as exc:
            last_error = exc
            logger.warning(
                "  [%s] chunk %d returned non-JSON (attempt %d/%d): %s",
                document_id,
                chunk_index,
                attempt,
                attempts,
                exc,
            )
    assert last_error is not None
    raise last_error
