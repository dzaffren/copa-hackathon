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


def _current_document_id(document_ids: list[str]) -> str:
    """The current (non-superseded) version is the last-declared one."""
    return document_ids[-1]


def _build_nodes(
    documents: dict,
    ids_by_policy: dict[str, list[str]],
    draft_registry: dict,
) -> list[GraphNode]:
    live_drafts = set(draft_registry.get("live_drafts", []))
    nodes: list[GraphNode] = []

    for policy_id, document_ids in ids_by_policy.items():
        current_id = _current_document_id(document_ids)
        for document_id in document_ids:
            doc = documents[document_id]
            if document_id != current_id:
                status = "Superseded"
            elif policy_id in live_drafts:
                status = "In progress"
            else:
                status = "In force"

            nodes.append(
                {
                    "id": document_id,
                    "policy_id": policy_id,
                    "title": doc["title"],
                    "version": doc["version"],
                    "status": status,
                    "cluster": doc["cluster"],
                }
            )

    return nodes


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


_VALID_PROVENANCE = {"structural", "curated", "llm-found"}


def _validate_non_lineage_edge(edge: dict, clause_index) -> None:
    reason = edge.get("reason")
    if not reason:
        raise GraphBuildError(
            f"Edge {edge.get('source')} -> {edge.get('target')} "
            f"(type={edge.get('type')}) has no reason"
        )

    for side in ("source_clauses", "target_clauses"):
        clauses = edge.get(side) or []
        if not clauses:
            raise GraphBuildError(
                f"Edge {edge.get('source')} -> {edge.get('target')} "
                f"(type={edge.get('type')}) has no {side}"
            )
        for clause_number in clauses:
            if clause_index.get(clause_number) is None:
                raise GraphBuildError(
                    f"Edge {edge.get('source')} -> {edge.get('target')} "
                    f"(type={edge.get('type')}) cites clause "
                    f"'{clause_number}' which does not resolve in the "
                    f"clause index"
                )

    provenance = edge.get("provenance")
    if provenance not in _VALID_PROVENANCE:
        raise GraphBuildError(
            f"Edge {edge.get('source')} -> {edge.get('target')} has invalid "
            f"provenance '{provenance}' (must be one of {_VALID_PROVENANCE})"
        )

    confidence = edge.get("confidence")
    if confidence is None or not (0.0 <= confidence <= 1.0):
        raise GraphBuildError(
            f"Edge {edge.get('source')} -> {edge.get('target')} has invalid "
            f"confidence '{confidence}' (must be in [0.0, 1.0])"
        )
    if provenance in ("structural", "curated") and confidence != 1.0:
        raise GraphBuildError(
            f"Edge {edge.get('source')} -> {edge.get('target')} has "
            f"provenance '{provenance}' but confidence {confidence} != 1.0"
        )


def _build_curated_edges(
    curated_edges: list[dict],
    ids_by_policy: dict[str, list[str]],
    clause_index,
) -> list[GraphEdge]:
    edges: list[GraphEdge] = []
    for curated in curated_edges:
        source_id = _current_document_id(ids_by_policy[curated["source_policy_id"]])
        target_id = _current_document_id(ids_by_policy[curated["target_policy_id"]])
        edge: GraphEdge = {
            "source": source_id,
            "target": target_id,
            "type": curated["type"],
            "reason": curated["reason"],
            "source_clauses": curated["source_clauses"],
            "target_clauses": curated["target_clauses"],
            "provenance": curated["provenance"],
            "confidence": curated["confidence"],
        }
        _validate_non_lineage_edge(edge, clause_index)
        edges.append(edge)
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
    nodes = _build_nodes(documents, ids_by_policy, draft_registry)
    edges = _build_version_lineage_edges(ids_by_policy)
    edges.extend(_build_curated_edges(curated_edges, ids_by_policy, clause_index))

    # Determinism of the frozen contract (spec Solution Design, "Build &
    # operability"): edges sort by (source, target, type) so a rebuild from
    # the same corpus produces byte-stable artifacts.
    edges.sort(key=lambda edge: (edge["source"], edge["target"], edge["type"]))

    return {"nodes": nodes, "edges": edges}
