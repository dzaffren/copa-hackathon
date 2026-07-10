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

from typing import Any, NotRequired, Optional, TypedDict, cast


class GraphNode(TypedDict):
    id: str
    policy_id: str
    title: str
    version: str
    status: str
    cluster: str
    # `kind` distinguishes internal policy nodes from external reference nodes
    # (#26). Every node carries it ("policy" by default — backward compatible:
    # a consumer that ignores `kind` is unaffected). The four fields below are
    # present ONLY on reference nodes (`kind == "reference"`).
    kind: NotRequired[str]
    source_type: NotRequired[str]  # peer_regulator|act|standard|handbook|trend
    access: NotRequired[str]  # public | restricted
    preview: NotRequired[bool]  # true → labelled preview band, no verbatim excerpt
    source_url: NotRequired[str]  # public references only


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

            node: GraphNode = {
                "id": document_id,
                "policy_id": policy_id,
                "title": doc["title"],
                "version": doc["version"],
                "status": status,
                "cluster": doc["cluster"],
                "kind": doc.get("kind", "policy"),
            }
            if node["kind"] == "reference":
                node["source_type"] = doc["source_type"]
                node["access"] = doc["access"]
                node["preview"] = doc["preview"]
                if doc.get("source_url"):
                    node["source_url"] = doc["source_url"]
            nodes.append(node)

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


def _validate_non_lineage_edge(
    edge: dict[str, Any],
    clause_index: Any,
    skip_target_clause_resolution: bool = False,
) -> None:
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
        # Reference-edge carve-out (#26): a restricted (handbook) or preview
        # (trend) target's `target_clauses` is a provenance LABEL, not an
        # ingested clause — its passage is intentionally never in the index, so
        # skip the resolution check for it (still required: non-empty + reason).
        # Source clauses, and every PUBLIC target clause, are always resolved —
        # an unresolved public reference passage still fails the build loudly.
        if side == "target_clauses" and skip_target_clause_resolution:
            continue
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
    curated_edges: list[dict[str, Any]],
    ids_by_policy: dict[str, list[str]],
    clause_index: Any,
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
        _validate_non_lineage_edge(cast(dict[str, Any], edge), clause_index)
        edges.append(edge)
    return edges


def _build_reference_edges(
    reference_edges: list[dict[str, Any]],
    ids_by_policy: dict[str, list[str]],
    documents: dict,
    clause_index: Any,
) -> list[GraphEdge]:
    """Assemble `type:"references"` edges (#26) from the draft to each external
    reference node.

    Endpoints resolve from `source_policy_id`/`target_policy_id` to that policy's
    current document, exactly like a curated edge. Validation applies the
    restricted/preview carve-out: when the target node is `access=="restricted"`
    or `preview is True`, its `target_clauses` label is not required to resolve
    (its passage is never ingested); every public reference target is fully
    resolved, so an unresolved public passage still raises `GraphBuildError`.
    """
    edges: list[GraphEdge] = []
    for ref in reference_edges:
        source_id = _current_document_id(ids_by_policy[ref["source_policy_id"]])
        target_id = _current_document_id(ids_by_policy[ref["target_policy_id"]])
        edge: GraphEdge = {
            "source": source_id,
            "target": target_id,
            "type": ref["type"],
            "reason": ref["reason"],
            "source_clauses": ref["source_clauses"],
            "target_clauses": ref["target_clauses"],
            "provenance": ref["provenance"],
            "confidence": ref["confidence"],
        }
        target_doc = documents[target_id]
        skip = (
            target_doc.get("access") == "restricted"
            or bool(target_doc.get("preview"))
        )
        _validate_non_lineage_edge(
            cast(dict[str, Any], edge),
            clause_index,
            skip_target_clause_resolution=skip,
        )
        edges.append(edge)
    return edges


def build_graph(
    documents: dict,
    curated_edges: list[dict[str, Any]],
    clause_index: Any,
    draft_registry: dict,
    llm_found_edges: Optional[list[dict[str, Any]]] = None,
    reference_edges: Optional[list[dict[str, Any]]] = None,
) -> dict:
    """Assemble `graph.json`'s `{"nodes": [...], "edges": [...]}` shape.

    `documents` may include external reference entries (`kind:"reference"`, #26)
    alongside the internal policy documents — reference nodes are emitted with
    their `source_type`/`access`/`preview`/`source_url`, and `reference_edges`
    (`type:"references"`) connect the draft to them.
    """
    ids_by_policy = _ordered_document_ids_by_policy(documents)
    nodes = _build_nodes(documents, ids_by_policy, draft_registry)
    edges = _build_version_lineage_edges(ids_by_policy)
    edges.extend(_build_curated_edges(curated_edges, ids_by_policy, clause_index))

    if reference_edges:
        edges.extend(
            _build_reference_edges(
                reference_edges, ids_by_policy, documents, clause_index
            )
        )

    if llm_found_edges:
        for edge in llm_found_edges:
            _validate_non_lineage_edge(edge, clause_index)
            edges.append(cast(GraphEdge, dict(edge)))

    # Determinism of the frozen contract (spec Solution Design, "Build &
    # operability"): edges sort by (source, target, type) so a rebuild from
    # the same corpus produces byte-stable artifacts.
    edges.sort(key=lambda edge: (edge["source"], edge["target"], edge["type"]))

    return {"nodes": nodes, "edges": edges}
