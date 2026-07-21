"""Every document_id declared on a workstream graph node must be a real
ingested document (present in the clause index), so the live analyze route
never resolves a node to a document with zero clauses."""
import json
from pathlib import Path

from engine.clauses import load_clause_index
from engine.config import REPO_ROOT

WORKSTREAMS = REPO_ROOT / "data" / "workstreams"
ARTIFACTS = REPO_ROOT / "data" / "artifacts"

EXPECTED = {
    ("opres-v2", "opres-pd-v0-3"): "opres-v1-2025-draft",
    ("opres-v2", "opres-dp-2025"): "opres-v1-2025-draft",
    ("opres-v2", "rmit-pd-2025"): "rmit-v2-2025",
    ("open-finance-ed", "of-ed-2025"): "open-finance-v1-2025-ed",
    ("open-finance-ed", "rmit-pd-2023"): "rmit-v1-2023",
    ("open-finance-ed", "bcm-pd-2022"): "bcm-v1-2022",
    ("rmit-v2-2025", "rmit-pd-v2"): "rmit-v2-2025",
    ("outsourcing-v2", "outsourcing-pd-v2"): "outsourcing-v1-2019",
    ("_cross", "of-ed-2025"): "open-finance-v1-2025-ed",
    ("_cross", "opres-dp-2025"): "opres-v1-2025-draft",
}


def _node(ws: str, node_id: str) -> dict:
    graph = json.loads((WORKSTREAMS / ws / "graph.json").read_text("utf-8"))
    return next(n for n in graph["nodes"] if n["id"] == node_id)


def test_declared_document_ids_match_expected():
    for (ws, node_id), doc_id in EXPECTED.items():
        assert _node(ws, node_id).get("document_id") == doc_id, (ws, node_id)


def test_declared_document_ids_are_ingested():
    index = load_clause_index(ARTIFACTS)
    for (ws, node_id), doc_id in EXPECTED.items():
        assert index.entries_for_document(doc_id), f"{doc_id} has no clauses"
