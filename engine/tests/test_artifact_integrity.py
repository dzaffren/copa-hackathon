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

# The OpRes DP × Open Finance ED trace cites 48 distinct clauses; 47 resolve.
# `Operational Resilience 3.3(e)` does not, and that is a known, bounded gap
# rather than a regression: the committed index was Document Intelligence-built,
# while the offline rule-based extractor does not split that sub-clause. It is
# pinned here so the number cannot quietly grow — if a third clause stops
# resolving, this fails.
KNOWN_UNRESOLVABLE = {"Operational Resilience 3.3(e)"}


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


def test_trace_was_fully_supported_when_it_ran(index):
    """The finder+critic marked all 12 linkages supported at record time."""
    trace = json.loads(OPRES_OF_TRACE.read_text(encoding="utf-8"))
    assert len(trace["validation"]) == 12
    assert all(e["supported"] for e in trace["validation"])


def test_workstream_fixtures_never_collide_with_the_index(index):
    """The fictional draft must not squat on a real document's clause numbers.

    `opres-v2`'s task node is an invented "OpRes PD v0.3" working draft. The real
    parsed OpRes Discussion Paper defines 1.1 / 2.1 / 4.4 / 5.3 / 7.1 too, with
    completely different text. While the index held no OpRes at all, a lookup of
    a fixture number was a clean KeyError; once the DP is indexed, the same
    lookup would return real text that contradicts what the review screen shows.

    A wrong answer is worse than a missing one, so the fixture clauses are
    namespaced "OpRes PD ..." — the convention the fixtures already used for
    "RMiT PD 1.2" vs the index's real "RMiT 1.2".
    """
    fixtures = (REPO_ROOT / "data" / "workstreams").glob("*/findings/*.json")
    collisions = []
    for path in fixtures:
        for finding in json.loads(path.read_text(encoding="utf-8")):
            for side in ("source_clauses", "target_clauses"):
                for clause in finding.get(side) or []:
                    if clause["clause_number"] in index:
                        collisions.append(f"{path.name}: {clause['clause_number']}")
    assert not collisions, (
        "Workstream fixture clause numbers collide with real indexed clauses. "
        "Namespace the fixture's (e.g. 'OpRes PD 5.3'), or a lookup returns text "
        f"the fixture does not say: {collisions}"
    )
