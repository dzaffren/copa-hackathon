"""Evidence probe: run the REAL finder pipeline on the demo cross-workstream pair
and report what it produces, so we can judge (with evidence, not a guess) whether
a genuinely-live Analyze is demo-quality — before wiring a document-id alias map
into the API.

WHY THIS EXISTS
The workstream graphs reference documents by ids like `opres-v1-2025-draft`, but
the committed anchor index (`data/artifacts/anchor-index.json`) keys the same
documents as `bnm-operational-resilience-dp-dec2025`. The two namespaces are
disjoint, so a live Analyze on the demo edge currently resolves to zero anchors
and returns nothing. This probe bypasses the API and calls the pipeline directly
with the CORRECT index ids (the alias targets), to see the findings a live path
WOULD produce once the alias map is added.

REQUIRES LIVE CREDENTIALS (this is the whole point — it calls the model):
    AZURE_FOUNDRY_ENDPOINT and AZURE_FOUNDRY_API_KEY must be set in the env.

USAGE (from repo root, on a machine with creds):
    PYTHONPATH=. .venv/bin/python -m scripts.probe_live_analyze
    PYTHONPATH=. .venv/bin/python -m scripts.probe_live_analyze --max-anchors 20
    PYTHONPATH=. .venv/bin/python -m scripts.probe_live_analyze --pair opres-rmit

`--max-anchors N` truncates each document to its first N anchors for a CHEAP first
look (fewer model calls); omit it for a full, faithful run. A capped run judges
quality on a sample only — if the sample looks good, re-run uncapped before
trusting latency numbers.
"""

import argparse
import json
import time
from pathlib import Path

from engine.anchors import Anchor, AnchorIndex
from engine.finder_pipeline import run_finder_pipeline
from engine.config import REPO_ROOT

# The demo document pairs, expressed as (label, doc_a index-id, doc_b index-id).
# doc_a is "ours"/the task side. These index-ids are the alias targets confirmed
# to resolve in data/artifacts/anchor-index.json.
PAIRS = {
    "opres-openfinance": (
        "OpRes DP  x  Open Finance ED  (the cross-workstream climax)",
        "bnm-operational-resilience-dp-dec2025",
        "bnm-open-finance-ed-2025",
    ),
    "opres-rmit": (
        "OpRes DP  x  RMiT (Nov 2025)  (a single-workstream edge)",
        "bnm-operational-resilience-dp-dec2025",
        "bnm-rmit-nov25",
    ),
}


def _index(max_anchors: int | None) -> AnchorIndex:
    raw = json.loads(
        (REPO_ROOT / "data" / "artifacts" / "anchor-index.json").read_text(
            encoding="utf-8"
        )
    )
    if max_anchors is None:
        return AnchorIndex(raw)
    # Keep only the first `max_anchors` anchors per document for a cheap look.
    kept: list[Anchor] = []
    seen: dict[str, int] = {}
    for a in raw:
        d = a["document_id"]
        if seen.get(d, 0) >= max_anchors:
            continue
        seen[d] = seen.get(d, 0) + 1
        kept.append(a)
    return AnchorIndex(kept)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", choices=list(PAIRS), default="opres-openfinance")
    ap.add_argument(
        "--max-anchors",
        type=int,
        default=None,
        help="Truncate each document to its first N anchors (cheap look).",
    )
    args = ap.parse_args()

    label, doc_a, doc_b = PAIRS[args.pair]
    index = _index(args.max_anchors)
    n_a = len(index.by_document(doc_a))
    n_b = len(index.by_document(doc_b))

    print(f"\n=== LIVE ANALYZE PROBE: {label} ===")
    print(f"doc_a = {doc_a}  ({n_a} anchors)")
    print(f"doc_b = {doc_b}  ({n_b} anchors)")
    if args.max_anchors is not None:
        print(f"(capped to first {args.max_anchors} anchors/doc — SAMPLE ONLY)")
    if n_a == 0 or n_b == 0:
        raise SystemExit("One side has 0 anchors — check the index / ids.")

    started = time.monotonic()
    try:
        result = run_finder_pipeline(index, doc_a, doc_b)
    except Exception as exc:  # noqa: BLE001 — surface any failure plainly
        print(f"\nPIPELINE FAILED: {type(exc).__name__}: {exc}")
        print(
            "If this is a credentials error, set AZURE_FOUNDRY_ENDPOINT / "
            "AZURE_FOUNDRY_API_KEY and re-run."
        )
        raise SystemExit(1) from exc
    elapsed = time.monotonic() - started

    connections = result.get("connections", [])
    unsupported = result.get("unsupported", [])
    print(f"\n--- RESULT in {elapsed:.1f}s ---")
    print(f"supported connections: {len(connections)}")
    print(f"unsupported (dropped): {len(unsupported)}")
    labels: dict[str, int] = {}
    for c in connections:
        labels[c.get("label", "?")] = labels.get(c.get("label", "?"), 0) + 1
    print(f"label mix: {labels}")

    print("\n--- FINDINGS (judge quality + verbatim citation) ---")
    for i, c in enumerate(connections, 1):
        print(f"\n[{i}] {c.get('label')}  (sentiment={c.get('sentiment')})")
        print(f"    summary: {c.get('summary')}")
        for side in ("source_clauses", "target_clauses"):
            for cl in c.get(side) or []:
                txt = (cl.get("text") or "").replace("\n", " ")[:120]
                print(f"    {side[:6]}: [{cl.get('clause_number')}] {txt!r}")

    print(
        "\nJUDGE: Are the labels right? Do the summaries read like a policy "
        "analyst wrote them? Is every cited clause real, verbatim, and relevant? "
        "Is the latency acceptable for a live on-stage click?"
    )


if __name__ == "__main__":
    main()
