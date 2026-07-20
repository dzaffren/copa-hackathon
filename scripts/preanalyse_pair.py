#!/usr/bin/env python3
"""Run find_connections on one document pair and persist a seed findings file.

This is a one-off prerequisite script for seeding the open-finance MVP1
demo workstream. It calls the real finder/critic LLM (Azure AI Foundry)
against two documents already indexed in `data/artifacts/anchor-index.json`,
and writes the result to `data/workstreams/{workstream_id}/findings/{edge_id}.json`
so the frontend can render pre-analysed edges on landing without a live
LLM call at demo time.

Also writes the raw connection trace to `data/artifacts/connection-trace-*.json`
via the engine's own trace writer (the demo backstop / audit trail).

Usage:
    .venv/bin/python scripts/preanalyse_pair.py \\
        --workstream open-finance-mvp1 \\
        --edge-id e-bispap168--ed \\
        --doc-a bis-pap168-open-finance \\
        --doc-b bnm-open-finance-ed-2025

Not part of the engine test suite — this is a wrapper around
`engine.connections.find_connections`. The engine module remains untouched.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Allow invocation from any cwd — put repo root on sys.path before engine imports.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from engine.anchors import Anchor, AnchorIndex  # noqa: E402
from engine.connections import find_connections  # noqa: E402

logger = logging.getLogger(__name__)

ANCHOR_INDEX_PATH = REPO_ROOT / "data" / "artifacts" / "anchor-index.json"
TRACE_DIR = REPO_ROOT / "data" / "artifacts"


def load_anchor_index() -> AnchorIndex:
    """Load the persisted AnchorIndex from disk."""
    if not ANCHOR_INDEX_PATH.exists():
        raise FileNotFoundError(
            f"{ANCHOR_INDEX_PATH} not found; run `python -m engine.build --anchors-only` first"
        )
    raw: list[Anchor] = json.loads(ANCHOR_INDEX_PATH.read_text(encoding="utf-8"))
    return AnchorIndex(raw)


def preanalyse(
    workstream_id: str,
    edge_id: str,
    doc_a_id: str,
    doc_b_id: str,
) -> None:
    """Run find_connections on the pair and write findings + trace."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    anchor_index = load_anchor_index()
    a_count = len(anchor_index.by_document(doc_a_id))
    b_count = len(anchor_index.by_document(doc_b_id))
    if a_count == 0:
        raise ValueError(f"no anchors for doc_a_id={doc_a_id!r} in {ANCHOR_INDEX_PATH}")
    if b_count == 0:
        raise ValueError(f"no anchors for doc_b_id={doc_b_id!r} in {ANCHOR_INDEX_PATH}")
    logger.info(
        "preanalyse: %s (%d anchors) × %s (%d anchors) → edge %s",
        doc_a_id,
        a_count,
        doc_b_id,
        b_count,
        edge_id,
    )

    result = find_connections(
        doc_a_id=doc_a_id,
        doc_b_id=doc_b_id,
        anchor_index=anchor_index,
        output_dir=TRACE_DIR,
    )

    findings = result["connections"]
    unsupported = result["unsupported"]
    logger.info(
        "preanalyse: got %d supported findings, %d unsupported",
        len(findings),
        len(unsupported),
    )

    findings_dir = REPO_ROOT / "data" / "workstreams" / workstream_id / "findings"
    findings_dir.mkdir(parents=True, exist_ok=True)
    findings_path = findings_dir / f"{edge_id}.json"

    # Shape to write matches what the workstream-graph GET /edges/{id} endpoint
    # will read from disk: a top-level object with the findings array.
    payload = {
        "edge_id": edge_id,
        "doc_a_id": doc_a_id,
        "doc_b_id": doc_b_id,
        "findings": findings,
        "unsupported": unsupported,
    }
    findings_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("preanalyse: wrote %s", findings_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workstream", required=True, help="workstream_id (e.g. open-finance-mvp1)"
    )
    parser.add_argument(
        "--edge-id", required=True, help="edge_id used as findings filename"
    )
    parser.add_argument("--doc-a", required=True, help="document_id of side A")
    parser.add_argument("--doc-b", required=True, help="document_id of side B")
    args = parser.parse_args()

    try:
        preanalyse(
            workstream_id=args.workstream,
            edge_id=args.edge_id,
            doc_a_id=args.doc_a,
            doc_b_id=args.doc_b,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("preanalyse failed: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
