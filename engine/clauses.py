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

from typing import Optional, TypedDict

from engine.config import AZURE_FOUNDRY_API_KEY, AZURE_FOUNDRY_ENDPOINT, PARSER_DEPLOYMENT

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


class ClauseAnchorNotFoundError(Exception):
    """Raised when an anchor's `starts_with` snippet is absent from the markdown."""


class ClauseAnchorAmbiguousError(Exception):
    """Raised when an anchor's `starts_with` snippet matches more than once."""


class ClauseCompletenessError(Exception):
    """Raised when the emitted clause set does not cover the expected clauses."""


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


def _trim_trailing_label(markdown: str, end: int, next_bare_number: Optional[str]) -> int:
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
        occurrences = markdown.count(snippet)
        if occurrences == 0:
            raise ClauseAnchorNotFoundError(
                f"Anchor for clause '{anchor['clause_number']}' "
                f"(starts_with={snippet!r}) not found in document "
                f"'{document_id}'"
            )
        if occurrences > 1:
            raise ClauseAnchorAmbiguousError(
                f"Anchor for clause '{anchor['clause_number']}' "
                f"(starts_with={snippet!r}) is ambiguous — found "
                f"{occurrences} times in document '{document_id}'"
            )
        positions.append(markdown.index(snippet))

    entries: dict[str, ClauseEntry] = {}
    children_by_parent: dict[str, list[str]] = {}
    raw_start_by_clause: dict[str, int] = {}
    raw_end_by_clause: dict[str, int] = {}

    for i, anchor in enumerate(anchors):
        start = positions[i]
        raw_end = positions[i + 1] if i + 1 < len(anchors) else len(markdown)
        next_bare_number = anchors[i + 1]["clause_number"] if i + 1 < len(anchors) else None
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


class ClausePrimaryIndexCollisionError(Exception):
    """Raised when two documents at equal precedence both claim the primary
    (current) slot for the same clause_number — an ambiguous collision that
    must never be silently resolved by picking one."""


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

        winner_entry = dict(by_document[winner_document_id])
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

    def get(self, clause_number: str, version: Optional[str] = None) -> Optional[ClauseEntry]:
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

    def full_text(self, clause_number: str, version: Optional[str] = None) -> Optional[str]:
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


class ClauseVersionNotFoundError(Exception):
    """Raised when a clause_number is known but the requested version is not.

    Distinct from an unknown `clause_number` (which `ClauseIndex.get` reports
    as `None`) so the API layer (#6 Task 6) can tell `404 CLAUSE_NOT_FOUND`
    apart from `404 CLAUSE_VERSION_NOT_FOUND`.
    """


def find_clause_anchors(markdown: str, document_id: str) -> list[dict]:
    """Call the parser LLM (Azure AI Foundry, Claude) to find clause anchors.

    This is the network seam — real callers use this; tests never do (they
    stub anchors by hand and call `build_clause_index` directly). Not
    exercised in this task; wired for Task 3/6 to call at real build time.
    """
    from azure.ai.inference import ChatCompletionsClient
    from azure.core.credentials import AzureKeyCredential

    client = ChatCompletionsClient(
        endpoint=AZURE_FOUNDRY_ENDPOINT,
        credential=AzureKeyCredential(AZURE_FOUNDRY_API_KEY),
    )
    raise NotImplementedError(
        "find_clause_anchors is wired to Azure AI Foundry but not implemented "
        "in this task — no live credentials in this environment. Task 3/6 "
        "should implement the prompt + response parsing when Foundry access "
        "is available."
    )
