"""CLI entrypoint wiring stages 1-3: ingest -> parse clauses -> build graph.

Run as ``python -m engine.build``. Reads the locked demo cluster from
`engine.config.DOCUMENTS`, converts each document to clean markdown (stage
1, `engine.ingest.ingest_document`), parses it into a clause index (stage 2,
`engine.clauses.find_clause_anchors` + `build_clause_index`/
`merge_clause_indexes`), then assembles the knowledge graph (stage 3,
`engine.graph.build_graph`) and writes both artifacts to
`data/artifacts/`.

Stage 2's LLM anchor-finding (`find_clause_anchors`) requires live Azure
Foundry credentials that are not available in every environment; `run_build`
takes `ingest_fn`/`find_anchors_fn` as injectable seams so tests can stub
them (matching the no-network discipline in engine/tests/test_clauses.py
and engine/tests/test_graph.py) without this module depending on a test
double directly.
"""

import json
from pathlib import Path
from typing import Any, Callable, Union, cast

from engine.clauses import (
    ClauseIndex,
    build_clause_index,
    find_clause_anchors,
    merge_clause_indexes,
)
from engine.graph import build_graph
from engine.ingest import ingest_document

IngestFn = Callable[[Union[str, Path]], str]
FindAnchorsFn = Callable[[str, str], list[dict[str, Any]]]


def run_build(
    documents: dict[str, dict[str, Any]],
    curated_edges: list[dict[str, Any]],
    draft_registry: dict[str, Any],
    output_dir: Path,
    ingest_fn: IngestFn = ingest_document,
    find_anchors_fn: FindAnchorsFn = find_clause_anchors,
) -> None:
    """Run stages 1-3 and write `clause-index.json` + `graph.json`.

    Args:
        documents: the document manifest, shaped like `engine.config.DOCUMENTS`.
        curated_edges: shaped like `engine.config.CURATED_SEED_EDGES`.
        draft_registry: `{"live_drafts": [policy_id, ...]}`.
        output_dir: directory to write the two artifacts into (created if
            it does not exist).
        ingest_fn: stage 1 — converts a source path to markdown. Defaults
            to `engine.ingest.ingest_document`; tests inject a stub.
        find_anchors_fn: stage 2 — finds clause anchors in a document's
            markdown. Defaults to `engine.clauses.find_clause_anchors`
            (requires live Azure Foundry credentials); tests inject a stub.
    """
    # The last document declared for a policy_id is its current version —
    # the version_lineage/status rules in graph.py rely on this same
    # ordering, so stage 2 uses it too when picking the primary-index winner.
    current_document_id_by_policy: dict[str, str] = {}
    for document_id, doc in documents.items():
        current_document_id_by_policy[doc["policy_id"]] = document_id

    document_entries: list[tuple[str, dict]] = []
    for document_id, doc in documents.items():
        markdown = ingest_fn(doc["source_path"])
        anchors = find_anchors_fn(markdown, document_id)
        entries = build_clause_index(
            anchors=anchors,
            markdown=markdown,
            document_id=document_id,
            policy_id=doc["policy_id"],
            source=doc["source"],
        )
        document_entries.append((document_id, entries))

    entries_by_policy: dict[str, list[tuple[str, dict]]] = {}
    for document_id, entries in document_entries:
        policy_id = documents[document_id]["policy_id"]
        entries_by_policy.setdefault(policy_id, []).append((document_id, entries))

    primary: dict[str, Any] = {}
    versions: dict[str, dict] = {}
    for policy_id, entries_for_policy in entries_by_policy.items():
        policy_primary, policy_versions = merge_clause_indexes(
            entries_for_policy,
            current_document_id=current_document_id_by_policy[policy_id],
        )
        primary.update(policy_primary)
        versions.update(policy_versions)

    clause_index = ClauseIndex(primary, versions)

    graph = build_graph(
        documents=documents,
        curated_edges=curated_edges,
        clause_index=clause_index,
        draft_registry=draft_registry,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "clause-index.json").write_text(
        json.dumps(primary, indent=2, sort_keys=True)
    )
    (output_dir / "graph.json").write_text(json.dumps(graph, indent=2))


def main() -> None:
    from engine.config import CURATED_SEED_EDGES, DOCUMENTS, REPO_ROOT

    draft_registry_path = REPO_ROOT / "data" / "draft_registry.json"
    draft_registry = json.loads(draft_registry_path.read_text())

    run_build(
        documents=cast(dict[str, dict[str, Any]], DOCUMENTS),
        curated_edges=cast(list[dict[str, Any]], CURATED_SEED_EDGES),
        draft_registry=draft_registry,
        output_dir=REPO_ROOT / "data" / "artifacts",
    )


if __name__ == "__main__":
    main()
