"""Fire the live finder/critic on the hero pair and pretty-print the result.

Demo-prep helper (NOT part of the build). Runs the real connection-finding
loop against the built clause index — a live Azure Claude call, so it needs the
Foundry credentials in `.env` (the same ones the build's ingestion used).

It calls `engine.connections.find_connections` directly (no HTTP server needed),
which writes `data/artifacts/connection-trace-<pair>.json` — the recorded proof
+ demo backstop. Then it prints a readable summary so you can eyeball whether
the RMiT 17.1 <-> Outsourcing 12.1 conflict was found and verbatim-cited.

Usage:
    uv run scripts/run_finder_trace.py
    uv run scripts/run_finder_trace.py <doc_a_id> <doc_b_id>   # any pair
"""

import sys
from pathlib import Path

# Make `engine` importable no matter how this file is launched (running a script
# by path puts scripts/ on sys.path, not the repo root). Prepend the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.clauses import load_clause_index  # noqa: E402
from engine.config import REPO_ROOT  # noqa: E402
from engine.connections import find_connections  # noqa: E402

DEFAULT_PAIR = ("rmit-v2-2025", "outsourcing-v1-2019")


def main() -> None:
    if len(sys.argv) == 3:
        doc_a, doc_b = sys.argv[1], sys.argv[2]
    elif len(sys.argv) == 1:
        doc_a, doc_b = DEFAULT_PAIR
    else:
        sys.exit("usage: run_finder_trace.py [<doc_a_id> <doc_b_id>]")

    artifacts_dir = REPO_ROOT / "data" / "artifacts"
    clause_index = load_clause_index(artifacts_dir)

    # Fail loudly on a document the index does not cover. The finder would
    # otherwise run happily against zero clauses, cost real model calls, and
    # record a trace of nothing — the silent-narrowing failure mode again
    # (docs/learnings/blocker-engine-build-silently-narrows-artifacts.md).
    for doc_id in (doc_a, doc_b):
        if not clause_index.entries_for_document(doc_id):
            sys.exit(
                f"No clauses indexed for '{doc_id}'. Build it first:\n"
                f"    PYTHONPATH=. python -m engine.build --docs {doc_a} {doc_b} "
                f"--output-dir <tmp> --merge\n"
                f"(a bare --docs build REPLACES the index — see --merge.)"
            )

    print(f"Running live finder+critic on:  {doc_a}  <->  {doc_b}")
    print("(this makes real Azure Claude calls — 2-3 round-trips, ~30-60s)\n")

    # finder_fn / critic_fn left as defaults => the real _finder_turn/_critic_turn
    # (live model). output_dir defaults to data/artifacts/ => trace written there.
    result = find_connections(doc_a, doc_b, clause_index)

    connections = result["connections"]
    unsupported = result["unsupported"]

    print(f"=== {len(connections)} SUPPORTED connection(s) ===\n")
    for i, c in enumerate(connections, 1):
        print(f"[{i}] {c['summary']}")
        if c.get("scope_note"):
            print(f"    scope: {c['scope_note']}")
        for side in ("source_clauses", "target_clauses"):
            for cite in c[side]:
                text = cite["text"].strip().replace("\n", " ")
                print(f"    {side[:-8]:>6}: {cite['clause_number']} — {text[:90]}")
        print()

    if unsupported:
        print(f"=== {len(unsupported)} UNSUPPORTED (dropped, never invented) ===")
        for u in unsupported:
            print(f"  - {u['summary']}  [{u['message']}]")
        print()

    pair = f"{doc_a}__{doc_b}"
    trace = artifacts_dir / f"connection-trace-{pair}.json"
    print(f"Trace written: {trace}" if Path(trace).exists() else "Trace NOT found!")

    # Hero check is only meaningful on the RMiT<->Outsourcing pair, where the
    # discovery brief hand-verified the 17.1<->12.1 conflict (RMiT 17.1 lives in
    # the in-force rmit-v2-2025; outsourcing-v1-2019 is the counterparty). For
    # any other pair (e.g. cross-workstream probes) we report a generic summary
    # and leave the "did it find the right thing" judgement to the human reader.
    if (doc_a, doc_b) == DEFAULT_PAIR:
        hero = any(
            any(cite["clause_number"] == "Outsourcing 12.1" for cite in c["target_clauses"])
            and any(cite["clause_number"] == "RMiT 17.1" for cite in c["source_clauses"])
            for c in connections
        )
        print(
            "\nHERO CONFLICT (RMiT 17.1 <-> Outsourcing 12.1): "
            + ("FOUND ✓" if hero else "NOT found — review finder/critic prompts")
        )
    else:
        print(
            f"\nSummary: {len(connections)} supported, {len(unsupported)} unsupported "
            f"— inspect above for the linkages you expected."
        )


if __name__ == "__main__":
    main()
