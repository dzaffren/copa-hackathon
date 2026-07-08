"""Tests for engine.build — CLI wiring of stages 1-3 (ingest -> clauses -> graph).

No network access: `ingest_fn` and `find_anchors_fn` are stubbed (matching
the pattern in test_clauses.py / test_graph.py of hand-written fixtures) so
the pipeline is exercised end-to-end without MarkItDown or the parser LLM.
This proves `build.py` is wired correctly; it is not run against the real
corpus in this environment (Task 2's `find_clause_anchors` remains a
NotImplementedError stub without live Foundry credentials).
"""

import json

from engine.build import run_build

OUTSOURCING_MARKDOWN = (
    "Outsourcing\n\n"
    "12 Approval for material outsourcing arrangements\n\n"
    "12.1 A financial institution must obtain the Bank's written approval "
    "before entering into a new material outsourcing arrangement.\n"
)

OUTSOURCING_ANCHORS = [
    {
        "clause_number": "12.1",
        "starts_with": "A financial institution must obtain the Bank's written approval",
        "heading": "12 Approval for material outsourcing arrangements",
        "parent": None,
    },
]

OPRES_MARKDOWN = (
    "Operational Resilience\n\n"
    "6 Critical operations\n\n"
    "6.11 A financial institution must maintain a register of critical "
    "cloud and third-party services.\n"
)

OPRES_ANCHORS = [
    {
        "clause_number": "6.11",
        "starts_with": "A financial institution must maintain a register",
        "heading": "6 Critical operations",
        "parent": None,
    },
]

FIXTURE_DOCUMENTS = {
    "outsourcing-v1-2019": {
        "policy_id": "outsourcing",
        "document_id": "outsourcing-v1-2019",
        "title": "Outsourcing",
        "version": "v1 · 2019",
        "source_path": "outsourcing.pdf",
        "source": "published",
        "cluster": "technology-risk",
    },
    "opres-v1-2025": {
        "policy_id": "opres",
        "document_id": "opres-v1-2025",
        "title": "Operational Resilience",
        "version": "v1 · 2025",
        "source_path": "opres.pdf",
        "source": "published",
        "cluster": "technology-risk",
    },
}

FIXTURE_CURATED_EDGES = [
    {
        "source_policy_id": "outsourcing",
        "target_policy_id": "opres",
        "type": "overlaps",
        "reason": "Both concern third-party arrangements for critical services.",
        "source_clauses": ["Outsourcing 12.1"],
        "target_clauses": ["Operational Resilience 6.11"],
        "provenance": "curated",
        "confidence": 1.0,
    },
]

FIXTURE_MARKDOWN_BY_PATH = {
    "outsourcing.pdf": OUTSOURCING_MARKDOWN,
    "opres.pdf": OPRES_MARKDOWN,
}

FIXTURE_ANCHORS_BY_DOCUMENT_ID = {
    "outsourcing-v1-2019": OUTSOURCING_ANCHORS,
    "opres-v1-2025": OPRES_ANCHORS,
}


def _stub_ingest_fn(path):
    return FIXTURE_MARKDOWN_BY_PATH[str(path)]


def _stub_find_anchors_fn(markdown, document_id):
    return FIXTURE_ANCHORS_BY_DOCUMENT_ID[document_id]


def test_run_build_writes_clause_index_and_graph_artifacts(tmp_path):
    output_dir = tmp_path / "artifacts"

    run_build(
        documents=FIXTURE_DOCUMENTS,
        curated_edges=FIXTURE_CURATED_EDGES,
        draft_registry={"live_drafts": ["opres"]},
        output_dir=output_dir,
        ingest_fn=_stub_ingest_fn,
        find_anchors_fn=_stub_find_anchors_fn,
    )

    clause_index_path = output_dir / "clause-index.json"
    graph_path = output_dir / "graph.json"
    assert clause_index_path.exists()
    assert graph_path.exists()

    clause_index = json.loads(clause_index_path.read_text())
    assert "Outsourcing 12.1" in clause_index
    assert clause_index["Outsourcing 12.1"]["text"].strip() == (
        "A financial institution must obtain the Bank's written approval "
        "before entering into a new material outsourcing arrangement."
    )

    graph = json.loads(graph_path.read_text())
    node_ids = {n["id"] for n in graph["nodes"]}
    assert node_ids == {"outsourcing-v1-2019", "opres-v1-2025"}
    non_lineage = [e for e in graph["edges"] if e["type"] != "version-lineage"]
    assert len(non_lineage) == 1
    assert non_lineage[0]["reason"]
