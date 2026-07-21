"""Project recorded connection traces into cross-workstream findings files.

Each registered pair's trace holds linkages found by a live finder+critic run,
but stores clause NUMBERS only, so its verbatim citations live or die with
`data/artifacts/clause-index.json`. That is exactly how they died once already
(#34; see docs/learnings/blocker-engine-build-silently-narrows-artifacts.md).

This script resolves the numbers to text ONCE, at build time, per registered
pair, and writes a findings file that embeds the quotes — the same guarantee
every other findings file in `data/workstreams/` carries, and the reason the
review screen can quote a clause without a live index. After this runs,
narrowing the index can no longer silently un-cite any projected pair.

Run:
    PYTHONPATH=. python scripts/project_cross_workstream_findings.py
    PYTHONPATH=. python scripts/project_cross_workstream_findings.py <edge_id> [<edge_id> ...]

Idempotent: re-running reproduces the same file(s), so any pair can be
re-run after a rebuild to pick up newly-resolvable clauses.
"""

import json
import sys
from typing import Any

from engine.config import REPO_ROOT

ARTIFACTS = REPO_ROOT / "data" / "artifacts"
CLAUSE_INDEX = ARTIFACTS / "clause-index.json"
CROSS_FINDINGS_DIR = REPO_ROOT / "data" / "workstreams" / "_cross" / "findings"

# What a clause card shows when the index cannot back it. The product rule is
# explicit: never invent a clause. A finding that cited something we can no
# longer quote says so, in place, rather than dropping the citation and
# pretending it was never made.
NO_MATCH = "No matching clause found"

# One entry per cross-workstream edge whose findings are projected from a
# recorded finder+critic trace. Add a new pair here (trace filename + the edge
# it becomes) rather than a new script — the edge's direction follows the
# trace, not necessarily the usual task-node-is-source convention (whichever
# side the critic wrote its summaries from).
PAIRS: list[dict[str, str]] = [
    {
        # The OpRes DP x Open Finance ED trace holds 12 cross-workstream
        # linkages found by a live finder+critic run (2026-07-11) — the demo's
        # climax and the evidence that retired this project's riskiest
        # assumption. Every summary is written from Open Finance's side
        # ("Open finance's ... goes beyond ..."), so flipping the endpoints
        # would leave the summaries reading backwards.
        "trace": "connection-trace-opres-v1-2025-draft__open-finance-v1-2025-ed.json",
        "edge_id": "x-open_finance_ed--opres_dp_2025",
    },
    {
        # BCM x Recovery Planning — the pain point named directly in product
        # feedback ("overlapping policies only discovered post-FPWG"). Indexed
        # by replaying cached ingest markdown (scripts/build_offline_replay_docs.py)
        # and traced live (scripts/run_finder_trace.py bcm-v1-2022
        # recovery-planning-v1-2021); this replaces the hand-authored demo mock
        # that previously stood in for this edge.
        "trace": "connection-trace-bcm-v1-2022__recovery-planning-v1-2021.json",
        "edge_id": "x-bcm_pd_2022--rrp_pd_v0_1",
    },
]


def _clause_text(index: dict[str, Any], number: str) -> str:
    """The verbatim quote for a clause number, or NO_MATCH.

    A clause that is *present but empty* counts as no match, and that case is
    real rather than theoretical: the offline extractor emits hollow entries
    for a small share of clauses where the Document Intelligence build had
    real prose. Treating "present" as "quotable" would put a clause number on
    screen with nothing underneath it — a citation that cites nothing, which
    is worse than admitting we cannot quote it.
    """
    entry = index.get(number)
    if entry is None:
        return NO_MATCH
    # `text` is the clause's own words; `_full_text` (present only on clauses
    # with children) also carries the sub-clauses. The citation is to the
    # clause itself, so `text` is the honest quote.
    text = " ".join((entry.get("text") or "").split())
    return text or NO_MATCH


def _clauses(index: dict[str, Any], numbers: list[str]) -> list[dict[str, str]]:
    return [{"clause_number": n, "text": _clause_text(index, n)} for n in numbers]


def _project(pair: dict[str, str], index: dict[str, Any]) -> None:
    trace_path = ARTIFACTS / pair["trace"]
    trace = json.loads(trace_path.read_text(encoding="utf-8"))

    critic = trace["critic_output"]
    validation = trace["validation"]
    assert len(critic) == len(validation), (
        f"{pair['trace']}: critic/validation length mismatch"
    )

    findings: list[dict[str, Any]] = []
    unresolved: list[str] = []
    for c, v in zip(critic, validation):
        assert c["summary"] == v["summary"], (
            f"{pair['trace']}: critic/validation misaligned"
        )
        source = _clauses(index, c["source_clauses"])
        target = _clauses(index, c["target_clauses"])
        unresolved += [
            x["clause_number"] for x in source + target if x["text"] == NO_MATCH
        ]
        findings.append(
            {
                "summary": c["summary"],
                "label": c["label"],
                "sentiment": c.get("sentiment"),
                "scope_note": c.get("scope_note"),
                "supported": v["supported"],
                "source_clauses": source,
                "target_clauses": target,
            }
        )

    out = CROSS_FINDINGS_DIR / f"{pair['edge_id']}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(findings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    total = sum(len(f["source_clauses"]) + len(f["target_clauses"]) for f in findings)
    print(f"wrote {len(findings)} findings -> {out.relative_to(REPO_ROOT)}")
    print(f"  clauses embedded: {total - len(unresolved)}/{total} verbatim")
    if unresolved:
        print(f"  unresolved (shown as '{NO_MATCH}'): {sorted(set(unresolved))}")


def main() -> None:
    index = json.loads(CLAUSE_INDEX.read_text(encoding="utf-8"))
    by_edge = {pair["edge_id"]: pair for pair in PAIRS}

    requested = sys.argv[1:] or list(by_edge)
    unknown = [edge_id for edge_id in requested if edge_id not in by_edge]
    if unknown:
        raise SystemExit(
            f"unknown edge id(s): {unknown}\nregistered: {sorted(by_edge)}"
        )

    for edge_id in requested:
        _project(by_edge[edge_id], index)


if __name__ == "__main__":
    main()
