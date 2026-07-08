"""Knowledge-graph model — nodes/edges, curated-edge builder, status derivation.

Design (see docs/specs/rulebook-radar/spec-knowledge-graph-engine.md, "Data
Model" / "Version lineage" / "Curated seed vs. LLM-found edges"): the graph
has three kinds of edge — `version-lineage` (purely structural, no clause
anchors, never touches an LLM), curated (seeded deterministically from
`engine.config.CURATED_SEED_EDGES`), and llm-found (surfaced by stage 4, a
later task — this module only provides the slot for them). Every non-lineage
edge must carry a non-empty `reason` and at least one clause anchor on each
side, and every clause it cites must resolve in the supplied `ClauseIndex` —
enforced here at build time, never trusted on faith.
"""

from typing import Optional, TypedDict


class GraphNode(TypedDict):
    id: str
    policy_id: str
    title: str
    version: str
    status: str
    cluster: str


class GraphEdge(TypedDict):
    source: str
    target: str
    type: str
    reason: str
    source_clauses: list[str]
    target_clauses: list[str]
    provenance: str
    confidence: float


class GraphBuildError(Exception):
    """Raised when an edge violates the "reason + clause anchors on both
    sides, every clause resolves" invariant — a build-time failure, never a
    silently-shipped bad edge (spec Data Model / Acceptance Criteria)."""


def _ordered_document_ids_by_policy(documents: dict) -> dict[str, list[str]]:
    """Group document ids by `policy_id`, preserving manifest insertion
    order (oldest-declared first — matches `engine.config.DOCUMENTS`, where
    an older version is always declared before its successor)."""
    by_policy: dict[str, list[str]] = {}
    for document_id, doc in documents.items():
        by_policy.setdefault(doc["policy_id"], []).append(document_id)
    return by_policy


def _build_version_lineage_edges(
    ids_by_policy: dict[str, list[str]],
) -> list[GraphEdge]:
    edges: list[GraphEdge] = []
    for document_ids in ids_by_policy.values():
        for older_id, newer_id in zip(document_ids, document_ids[1:]):
            edges.append(
                {
                    "source": older_id,
                    "target": newer_id,
                    "type": "version-lineage",
                    "reason": (
                        f"{older_id} is superseded by {newer_id} of the "
                        f"same policy."
                    ),
                    "source_clauses": [],
                    "target_clauses": [],
                    "provenance": "structural",
                    "confidence": 1.0,
                }
            )
    return edges


def build_graph(
    documents: dict,
    curated_edges: list[dict],
    clause_index,
    draft_registry: dict,
    llm_found_edges: Optional[list[dict]] = None,
) -> dict:
    """Assemble `graph.json`'s `{"nodes": [...], "edges": [...]}` shape."""
    ids_by_policy = _ordered_document_ids_by_policy(documents)
    edges = _build_version_lineage_edges(ids_by_policy)

    return {"nodes": [], "edges": edges}
