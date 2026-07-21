"""Index BCM + Recovery Planning into clause-index.json without touching Azure
Document Intelligence.

Both documents already have cached, DI-quality ingest markdown on disk at
data/artifacts/_ingest/{document_id}.md, written by an earlier full build (see
docs/learnings/convention-offline-build-needs-docintel.md — the reading-order
scramble that blocks an offline rebuild only bites at stage 1/ingest; stage 2
(engine.clauses.segment_clauses) is already network-free). This script replays
that cached markdown through the real pipeline instead of re-ingesting, then
merges the result into the committed clause-index.json via the same --merge
path engine.build.main() uses, so the "never silently narrow the index"
invariant (#34) holds.

Run:
    PYTHONPATH=. python scripts/build_offline_replay_docs.py
"""

import json
import tempfile
from pathlib import Path

from engine.build import _merge_clause_index, run_build
from engine.config import DOCUMENTS, REPO_ROOT

DOCUMENT_IDS = ["bcm-v1-2022", "recovery-planning-v1-2021"]
ARTIFACTS_DIR = REPO_ROOT / "data" / "artifacts"
INGEST_DIR = ARTIFACTS_DIR / "_ingest"


def main() -> None:
    documents = {doc_id: DOCUMENTS[doc_id] for doc_id in DOCUMENT_IDS}

    already_indexed = set(
        json.loads((ARTIFACTS_DIR / "clause-index.json").read_text(encoding="utf-8"))
    )

    # ingest_fn only ever receives `source_path`, so replaying cached markdown
    # for a *batch* needs a source_path -> document_id lookup; unambiguous here
    # since this batch's two documents have distinct source PDFs.
    doc_id_by_source_path = {
        str(doc["source_path"]): doc_id for doc_id, doc in documents.items()
    }

    def replay_cached_ingest(source_path) -> str:
        doc_id = doc_id_by_source_path[str(source_path)]
        cached = INGEST_DIR / f"{doc_id}.md"
        if not cached.exists():
            raise FileNotFoundError(
                f"no cached ingest markdown for {doc_id} at {cached} — this "
                "script only replays documents already ingested by a prior "
                "Document-Intelligence build; run a real ingest for this one."
            )
        return cached.read_text(encoding="utf-8")

    draft_registry = json.loads(
        (REPO_ROOT / "data" / "draft_registry.json").read_text(encoding="utf-8")
    )

    scratch_dir = Path(tempfile.mkdtemp(prefix="engine-build-replay-"))
    run_build(
        documents=documents,
        curated_edges=[],  # no curated edge in this repo connects bcm<->recovery-planning
        draft_registry=draft_registry,
        output_dir=scratch_dir,
        ingest_fn=replay_cached_ingest,
        reference_documents={},
        reference_edges=[],
    )

    added = _merge_clause_index(scratch_dir, ARTIFACTS_DIR)
    new_index = json.loads((ARTIFACTS_DIR / "clause-index.json").read_text(encoding="utf-8"))
    newly_added = sorted(set(new_index) - already_indexed)
    print(f"merged {added} clause(s) into {ARTIFACTS_DIR / 'clause-index.json'}")
    print(f"  {len(newly_added)} newly indexed clause number(s), e.g. {newly_added[:5]}")


if __name__ == "__main__":
    main()
