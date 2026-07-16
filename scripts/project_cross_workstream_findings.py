"""Project a recorded connection trace into a workstream findings file.

The OpRes DP × Open Finance ED trace holds 12 cross-workstream linkages found by
a live finder+critic run (2026-07-11). It is the demo's climax and the evidence
that retired this project's riskiest assumption — but it stores clause NUMBERS
only, so its verbatim citations live or die with `data/artifacts/clause-index.json`.
That is exactly how they died once already (#34; see
docs/learnings/blocker-engine-build-silently-narrows-artifacts.md).

This script resolves the numbers to text ONCE, at build time, and writes a
findings file that embeds the quotes — the same guarantee every other findings
file in `data/workstreams/` carries, and the reason the review screen can quote a
clause without a live index. After this runs, narrowing the index can no longer
silently un-cite the demo.

Run:
    PYTHONPATH=. python scripts/project_cross_workstream_findings.py

Idempotent: re-running reproduces the same file, so it can be re-run after a
rebuild to pick up newly-resolvable clauses.
"""

import json
from pathlib import Path
from typing import Any

from engine.config import REPO_ROOT

ARTIFACTS = REPO_ROOT / "data" / "artifacts"
TRACE = ARTIFACTS / "connection-trace-opres-v1-2025-draft__open-finance-v1-2025-ed.json"
CLAUSE_INDEX = ARTIFACTS / "clause-index.json"

# The cross-workstream edge this trace becomes. Direction follows the trace, not
# the usual task-node-is-source convention: the critic wrote every summary from
# Open Finance's side ("Open finance's ... goes beyond ..."), so flipping the
# endpoints would leave 12 summaries reading backwards.
EDGE_ID = "x-open_finance_ed--opres_dp_2025"
OUT = REPO_ROOT / "data" / "workstreams" / "_cross" / "findings" / f"{EDGE_ID}.json"

# What a clause card shows when the index cannot back it. The product rule is
# explicit: never invent a clause. A finding that cited something we can no
# longer quote says so, in place, rather than dropping the citation and
# pretending it was never made.
NO_MATCH = "No matching clause found"


def _clause_text(index: dict[str, Any], number: str) -> str:
    """The verbatim quote for a clause number, or NO_MATCH.

    A clause that is *present but empty* counts as no match, and that case is
    real rather than theoretical: the offline extractor emits hollow entries for
    ~29% of the OpRes DP (text `""`, heading full of footnote debris) where the
    Document Intelligence build had real prose. Treating "present" as "quotable"
    would put a clause number on screen with nothing underneath it — a citation
    that cites nothing, which is worse than admitting we cannot quote it.
    """
    entry = index.get(number)
    if entry is None:
        return NO_MATCH
    # `text` is the clause's own words; `_full_text` (present only on clauses
    # with children) also carries the sub-clauses. The citation is to the clause
    # itself, so `text` is the honest quote.
    text = " ".join((entry.get("text") or "").split())
    return text or NO_MATCH


def _clauses(index: dict[str, Any], numbers: list[str]) -> list[dict[str, str]]:
    return [{"clause_number": n, "text": _clause_text(index, n)} for n in numbers]


def main() -> None:
    trace = json.loads(TRACE.read_text(encoding="utf-8"))
    index = json.loads(CLAUSE_INDEX.read_text(encoding="utf-8"))

    critic = trace["critic_output"]
    validation = trace["validation"]
    assert len(critic) == len(validation), "critic/validation length mismatch"

    findings: list[dict[str, Any]] = []
    unresolved: list[str] = []
    for c, v in zip(critic, validation):
        assert c["summary"] == v["summary"], "critic/validation misaligned"
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

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(findings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    total = sum(len(f["source_clauses"]) + len(f["target_clauses"]) for f in findings)
    print(f"wrote {len(findings)} findings -> {OUT.relative_to(REPO_ROOT)}")
    print(f"  clauses embedded: {total - len(unresolved)}/{total} verbatim")
    if unresolved:
        print(f"  unresolved (shown as '{NO_MATCH}'): {sorted(set(unresolved))}")


if __name__ == "__main__":
    main()
