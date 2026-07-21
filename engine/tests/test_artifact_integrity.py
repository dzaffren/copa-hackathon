"""The clause index must actually back the citations that depend on it.

This suite exists because of a specific, recorded failure. #34 rebuilt
`data/artifacts/` without Azure Document Intelligence, silently shrinking the
clause index from 7 documents to 2 (RMiT only) and orphaning two committed
traces — and the whole suite stayed green through it, because nothing ever
re-resolved a citation. See
docs/learnings/blocker-engine-build-silently-narrows-artifacts.md.

So these tests re-resolve. They are the check that would have caught #34 at the
time, and they will catch the next narrowing.

Nothing here is skippable. A missing artifact is the failure, not a reason to
skip: an unverifiable citation and a wrong citation are the same product defect.
"""

import json
import re

import pytest

from engine.config import REPO_ROOT

ARTIFACTS = REPO_ROOT / "data" / "artifacts"
CLAUSE_INDEX = ARTIFACTS / "clause-index.json"
OPRES_OF_TRACE = (
    ARTIFACTS / "connection-trace-opres-v1-2025-draft__open-finance-v1-2025-ed.json"
)

# The OpRes DP × Open Finance ED trace cites 48 distinct clauses; 47 exist as
# keys. `Operational Resilience 3.3(e)` does not — the offline rule-based
# extractor does not split that sub-clause, where the Document Intelligence build
# did. Pinned so the number cannot quietly grow.
KNOWN_UNRESOLVABLE = {"Operational Resilience 3.3(e)"}

# Hollow entries: present as keys, but with empty `text`. These are WORSE than a
# missing clause — a lookup "succeeds" and yields nothing, so a citation renders
# as a clause number with no words under it. They exist because the offline
# extractor mis-segments the two draft PDFs (their headings are full of footnote
# debris), where Document Intelligence produced real prose. Even DI-built
# documents carry a small long-tail of deeply-nested sub-items DI cannot anchor
# (see BCM / Recovery Planning below) — so the budget is per-document, not zero.
#
# Ratios are pinned per document rather than asserted to be zero, because zero is
# not reachable offline and a test that cannot pass is a test that gets deleted.
# Rebuilding with Azure Document Intelligence is what fixes the offline case;
# until then the projection renders hollow clauses as "No matching clause found"
# rather than as an empty quote. RMiT is the control: it is DI-built, and 1/608
# is what good looks like.
MAX_HOLLOW = {
    "RMiT": 1,
    "Open Finance": 15,
    "Operational Resilience": 21,
    # BCM and Recovery Planning are DI-built (same class as the RMiT control):
    # a single deeply-nested sub-item each (BCM 9.2(c), Recovery Planning
    # 11.8(c)) sits among populated siblings where DI missed the last leaf —
    # the documented long-tail drop, not offline degradation. 1/246 and 1/258.
    "BCM": 1,
    "Recovery": 1,
}


@pytest.fixture(scope="module")
def index() -> dict:
    assert CLAUSE_INDEX.exists(), f"{CLAUSE_INDEX} is missing"
    return json.loads(CLAUSE_INDEX.read_text(encoding="utf-8"))


def _prefix_counts(index: dict) -> dict[str, int]:
    out: dict[str, int] = {}
    for key in index:
        head = key.split()[0]
        prefix = " ".join(key.split()[:2]) if head in {"Open", "Operational"} else head
        out[prefix] = out.get(prefix, 0) + 1
    return out


def test_index_covers_every_document_its_traces_cite(index):
    """The narrowing guard: RMiT alone is not enough."""
    counts = _prefix_counts(index)
    for document in ("RMiT", "Operational Resilience", "Open Finance"):
        assert counts.get(document, 0) > 0, (
            f"clause-index.json has no {document!r} clauses. A rebuild without "
            f"Azure Document Intelligence narrows the index — do not commit it. "
            f"Present: {counts}"
        )


def test_opres_x_openfinance_trace_still_resolves(index):
    """Every clause the cross-workstream trace cites resolves to real text.

    This is the demo climax's evidence: 12 linkages found by a live finder+critic
    run across two concurrent BNM workstreams, each verbatim-cited from both
    sides. The trace stores clause NUMBERS, not text, so the citations are only
    as good as the index behind them.
    """
    trace = json.loads(OPRES_OF_TRACE.read_text(encoding="utf-8"))
    cited = {
        clause["clause_number"]
        for entry in trace["validation"]
        for clause in entry["cited_clauses"]
    }
    unresolved = {c for c in cited if c not in index} - KNOWN_UNRESOLVABLE

    assert not unresolved, (
        f"{len(unresolved)} clause(s) the trace cites are not in the index: "
        f"{sorted(unresolved)}. The trace is orphaned — rebuild the index for "
        f"its documents rather than weakening this test."
    )


def test_the_known_gap_is_still_exactly_one_clause(index):
    """Pins KNOWN_UNRESOLVABLE honestly in both directions.

    If the gap is fixed (a Document Intelligence rebuild), this fails and the
    constant should shrink — a stale allowlist quietly excusing a real clause is
    how this kind of guard rots.
    """
    trace = json.loads(OPRES_OF_TRACE.read_text(encoding="utf-8"))
    cited = {
        clause["clause_number"]
        for entry in trace["validation"]
        for clause in entry["cited_clauses"]
    }
    still_missing = {c for c in KNOWN_UNRESOLVABLE if c in cited and c not in index}
    assert still_missing == KNOWN_UNRESOLVABLE, (
        "KNOWN_UNRESOLVABLE is stale — these now resolve, so remove them: "
        f"{KNOWN_UNRESOLVABLE - still_missing}"
    )


def test_indexed_clauses_are_not_hollow(index):
    """A clause that exists but says nothing is not a clause.

    This is the blind spot the previous guard had, and the one #34 slipped
    through in a different guise: checking that a document is *present* says
    nothing about whether its clauses carry text. A hollow entry turns a lookup
    into a silent empty quote — the citation equivalent of a wrong answer.
    """
    hollow: dict[str, list[str]] = {}
    for key, entry in index.items():
        if (entry.get("text") or "").strip():
            continue
        head = key.split()[0]
        prefix = " ".join(key.split()[:2]) if head in {"Open", "Operational"} else head
        hollow.setdefault(prefix, []).append(key)

    over = {
        prefix: (len(keys), MAX_HOLLOW.get(prefix, 0))
        for prefix, keys in hollow.items()
        if len(keys) > MAX_HOLLOW.get(prefix, 0)
    }
    assert not over, (
        "More clauses are hollow (present, but with empty text) than the pinned "
        f"budget allows: {over}. A rebuild without Azure Document Intelligence "
        "degrades extraction — rebuild with DI rather than raising the budget."
    )


def test_hollow_budgets_are_not_stale(index):
    """If a DI rebuild fixes extraction, MAX_HOLLOW should shrink to match.

    Pins the budget from below as well as above, so it records what IS rather
    than drifting into a permanent excuse.
    """
    actual: dict[str, int] = {p: 0 for p in MAX_HOLLOW}
    for key, entry in index.items():
        if (entry.get("text") or "").strip():
            continue
        head = key.split()[0]
        prefix = " ".join(key.split()[:2]) if head in {"Open", "Operational"} else head
        if prefix in actual:
            actual[prefix] += 1
    assert actual == MAX_HOLLOW, (
        f"MAX_HOLLOW is stale. Actual hollow counts: {actual}. If extraction "
        "improved, lower the budget to lock the gain in."
    )


def test_trace_was_fully_supported_when_it_ran(index):
    """The finder+critic marked all 12 linkages supported at record time."""
    trace = json.loads(OPRES_OF_TRACE.read_text(encoding="utf-8"))
    assert len(trace["validation"]) == 12
    assert all(e["supported"] for e in trace["validation"])


def test_a_fixture_clause_never_contradicts_the_indexed_clause_of_that_number(index):
    """One clause number must mean one thing.

    Two kinds of findings cite clauses, and the rule has to serve both:

    - The `_cross` findings quote REAL documents ("Open Finance 7.1"), projected
      straight out of the clause index. Their numbers *should* be in the index.
    - `opres-v2`'s task node is an invented "OpRes PD v0.3" draft. The real
      parsed OpRes Discussion Paper happens to define 1.1 / 2.1 / 4.4 / 5.3 /
      7.1 too, with completely different text. Its numbers must NOT be.

    So the invariant is not "never appears in the index" — it is: if a fixture
    cites a number the index also has, the text must agree. That catches the
    fictional draft squatting on a real document's numbering (the texts differ),
    while leaving genuine citations alone (the texts match).

    Why it matters: while the index held no OpRes at all, looking up a fixture
    number was a clean KeyError. Once the DP is indexed, the same lookup returns
    real text contradicting what the review screen shows for that number — a
    wrong answer where there used to be an obvious miss. The fix is the
    convention the fixtures already used for "RMiT PD 1.2" vs real "RMiT 1.2":
    namespace the fiction.
    """
    disagreements = []
    for path in (REPO_ROOT / "data" / "workstreams").glob("*/findings/*.json"):
        for finding in json.loads(path.read_text(encoding="utf-8")):
            for side in ("source_clauses", "target_clauses"):
                for clause in finding.get(side) or []:
                    entry = index.get(clause["clause_number"])
                    if entry is None:
                        continue  # not a real indexed clause — nothing to contradict
                    indexed = " ".join((entry.get("text") or "").split())
                    if not indexed:
                        # Hollow entry: the fixture correctly says "No matching
                        # clause found" where the index has nothing to offer.
                        # Not a contradiction — covered by the hollow tests.
                        continue
                    quoted = " ".join(clause["text"].split())
                    if indexed != quoted:
                        disagreements.append(
                            f"{path.name}: {clause['clause_number']}\n"
                            f"    fixture: {quoted[:70]}\n"
                            f"    indexed: {indexed[:70]}"
                        )
    assert not disagreements, (
        "A fixture quotes different text than the clause index holds for the "
        "same clause number. Either the quote drifted, or a fictional document "
        "is squatting on a real one's numbering — namespace it (e.g. "
        "'OpRes PD 5.3'):\n" + "\n".join(disagreements)
    )
