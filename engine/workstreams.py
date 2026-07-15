"""Workstream Brain — Graph Screen persistence helpers.

Read/write helpers over the per-workstream fixture store used by the Workstream
Graph hero screen (spec docs/specs/workstream-brain/spec-workstream-graph.md):

    data/workstreams/{id}/workstream.json   metadata + role + primary_task_id
    data/workstreams/{id}/graph.json        {"nodes": [...], "edges": [...]}
    data/workstreams/{id}/findings/{edge_id}.json   Connection[] per analysed edge

This module ADAPTS to the Task-Screen conventions already on disk (added by the
#36 merge): nodes carry `node_type`, edges carry `edge_type`, and an edge's
`analysed` flag / `findings_count` are DERIVED from the presence and length of
its findings file rather than stored in graph.json. The graph screen shows a
single draft in the centre with its anchors around it, so a workstream's
`primary_task_id` selects which task node the graph view is built around
(`primary_subgraph`), keeping the canvas to one PD + its anchors even when the
fixture also holds sibling drafts for the Task Screen.

All writes are UTF-8 (the corpus carries glyphs that crash the cp1252 platform
default on Windows — see docs/learnings/pattern-engine-artifact-writes-utf8.md).
"""

import json
import re
from pathlib import Path
from typing import Any, Optional, Union

# The seven flat node types and four structural edge types (spec Business Rules
# & Constraints). Type is picked once at add-time and validated here.
NODE_TYPES: frozenset[str] = frozenset(
    {
        "task",
        "internal-published",
        "international-standard",
        "peer-regulator",
        "act-law",
        "industry-input",
        "others",
    }
)
EDGE_TYPES: frozenset[str] = frozenset(
    {"supersedes", "references", "contributes-to", "parallel-to"}
)

# The demo pair whose "Analyze linkages" replays a canned, verbatim-cited result
# instead of a live model call (spec Dependencies — "Retired experiment trace").
# Matched order-independently: the edge runs OpRes PD v0.3 ↔ FSB Third-Party
# Toolkit in either direction.
_DEMO_ANALYZE_PAIR: frozenset[str] = frozenset({"opres-pd-v0-3", "fsb-3rd-party"})

# The canned findings for that pair. Every clause quoted here is verbatim from
# the OpRes working draft / FSB Toolkit (product rule: no invented clauses).
_DEMO_ANALYZE_FINDINGS: list[dict[str, Any]] = [
    {
        "summary": "Third-party register aligns with FSB Toolkit register expectations",
        "label": "aligns-with",
        "sentiment": None,
        "scope_note": None,
        "supported": True,
        "source_clauses": [
            {
                "clause_number": "Operational Resilience 4.5",
                "text": "A financial institution shall maintain a register of arrangements with third-party service providers that support critical operations.",
            }
        ],
        "target_clauses": [
            {
                "clause_number": "FSB Toolkit Tool 2",
                "text": "Financial institutions maintain a comprehensive register of third-party service relationships.",
            }
        ],
    },
    {
        "summary": "Draft mandates tested exit plans per critical provider, going beyond the FSB baseline",
        "label": "goes-beyond",
        "sentiment": None,
        "scope_note": "The FSB Toolkit expects dependency oversight but stops short of a tested per-provider exit plan.",
        "supported": True,
        "source_clauses": [
            {
                "clause_number": "Operational Resilience 4.7",
                "text": "A financial institution shall maintain a documented and periodically tested exit plan for each critical third-party service provider.",
            }
        ],
        "target_clauses": [
            {
                "clause_number": "FSB Toolkit Tool 6",
                "text": "Financial institutions consider exit strategies for critical third-party service relationships.",
            }
        ],
    },
    {
        "summary": "FSB covers third-party concentration risk; the draft is silent on concentration",
        "label": "silent-on",
        "sentiment": None,
        "scope_note": None,
        "supported": True,
        "source_clauses": [],
        "target_clauses": [
            {
                "clause_number": "FSB Toolkit Tool 7",
                "text": "Financial authorities monitor systemic third-party dependencies and concentration across the sector.",
            }
        ],
    },
]


def workstream_dir(root: Union[str, Path], workstream_id: str) -> Path:
    """The on-disk directory for one workstream."""
    return Path(root) / workstream_id


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    """UTF-8 write with a trailing newline (see module docstring on encoding)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def load_workstream(root: Union[str, Path], workstream_id: str) -> Optional[dict[str, Any]]:
    """Load `workstream.json`, or `None` when the workstream is unknown."""
    path = workstream_dir(root, workstream_id) / "workstream.json"
    return _read_json(path) if path.exists() else None


def load_graph(root: Union[str, Path], workstream_id: str) -> Optional[dict[str, Any]]:
    """Load `graph.json`, or `None` when the workstream (or its graph) is absent."""
    path = workstream_dir(root, workstream_id) / "graph.json"
    return _read_json(path) if path.exists() else None


def save_graph(root: Union[str, Path], workstream_id: str, graph: dict[str, Any]) -> None:
    """Persist `graph.json` (UTF-8)."""
    _write_json(workstream_dir(root, workstream_id) / "graph.json", graph)


def findings_path(root: Union[str, Path], workstream_id: str, edge_id: str) -> Path:
    return workstream_dir(root, workstream_id) / "findings" / f"{edge_id}.json"


def load_findings(
    root: Union[str, Path], workstream_id: str, edge_id: str
) -> Optional[list[dict[str, Any]]]:
    """The Connection[] for an edge, or `None` when the edge has no findings file
    (→ the edge is `not_analysed`)."""
    path = findings_path(root, workstream_id, edge_id)
    return _read_json(path) if path.exists() else None


def save_findings(
    root: Union[str, Path],
    workstream_id: str,
    edge_id: str,
    findings: list[dict[str, Any]],
) -> None:
    """Persist an edge's findings file (UTF-8); its presence flips the edge to
    `analysed` on the next graph read."""
    _write_json(findings_path(root, workstream_id, edge_id), findings)


def edge_is_analysed(root: Union[str, Path], workstream_id: str, edge_id: str) -> bool:
    """An edge is analysed iff its findings file exists (derived, not stored)."""
    return findings_path(root, workstream_id, edge_id).exists()


def list_workstreams(root: Union[str, Path]) -> list[dict[str, Any]]:
    """Project every workstream's `workstream.json` onto the sidebar list shape
    `{id, name, deliverable_type, role}`. Directories without a `workstream.json`
    are skipped. Sorted by directory name for a stable order."""
    root = Path(root)
    out: list[dict[str, Any]] = []
    if not root.exists():
        return out
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        meta_path = d / "workstream.json"
        if not meta_path.exists():
            continue
        ws = _read_json(meta_path)
        out.append(
            {
                "id": ws.get("id", d.name),
                "name": ws.get("name", d.name),
                "deliverable_type": ws.get("deliverable_type"),
                "role": ws.get("role"),
            }
        )
    return out


def primary_task_id(
    workstream: Optional[dict[str, Any]], graph: dict[str, Any]
) -> Optional[str]:
    """The task node the graph view is centred on: the workstream's declared
    `primary_task_id`, else the first `task` node in the graph."""
    if workstream and workstream.get("primary_task_id"):
        return workstream["primary_task_id"]
    for node in graph.get("nodes", []):
        if node.get("node_type") == "task":
            return node["id"]
    return None


def primary_subgraph(
    graph: dict[str, Any], task_id: Optional[str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """The (nodes, edges) reachable in one hop from `task_id` — the centre task
    node plus its incident anchors and the edges between them. Keeps the canvas
    to one draft + its anchors even when the fixture holds sibling drafts."""
    if task_id is None:
        return [], []
    edges = [
        e
        for e in graph.get("edges", [])
        if e.get("source") == task_id or e.get("target") == task_id
    ]
    keep: set[str] = {task_id}
    for e in edges:
        keep.add(e["source"])
        keep.add(e["target"])
    nodes = [n for n in graph.get("nodes", []) if n["id"] in keep]
    return nodes, edges


def neighbour_ids(edges: list[dict[str, Any]], node_id: str) -> list[str]:
    """The distinct node ids joined to `node_id` by any edge in `edges` (either
    direction), in first-seen order."""
    seen: set[str] = set()
    out: list[str] = []
    for e in edges:
        other: Optional[str] = None
        if e.get("source") == node_id:
            other = e.get("target")
        elif e.get("target") == node_id:
            other = e.get("source")
        if other is not None and other not in seen:
            seen.add(other)
            out.append(other)
    return out


def edges_between(
    edges: list[dict[str, Any]], node_ids: set[str], exclude_node: Optional[str] = None
) -> list[dict[str, Any]]:
    """Edges whose BOTH endpoints are in `node_ids`, in graph order.

    Backs the drafting workspace's "Related · 1 hop" tab: the linkages the task's
    anchors have with each other, as opposed to with the draft. `exclude_node`
    drops any edge touching that node, which is how the caller keeps the task's
    own edges out of a set that contains it.

    Note the seeded `opres-v2` fixture has no anchor↔anchor edges at all — every
    edge runs task → anchor — so this correctly returns [] there. That is a
    fixture gap, not a bug: seeding those edges means asserting what BCBS says
    about HKMA, and no source text for that exists in this repo.
    """
    out: list[dict[str, Any]] = []
    for e in edges:
        source, target = e.get("source"), e.get("target")
        if source not in node_ids or target not in node_ids:
            continue
        if exclude_node is not None and exclude_node in (source, target):
            continue
        out.append(e)
    return out


def slugify(text: str) -> str:
    """A lowercase, hyphen-joined id fragment from free text."""
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s or "node"


def make_node_id(title: str, existing_ids: set[str]) -> str:
    """A unique node id derived from the title, suffixed on collision."""
    base = slugify(title)
    node_id = base
    n = 2
    while node_id in existing_ids:
        node_id = f"{base}-{n}"
        n += 1
    return node_id


def make_edge_id(source: str, target: str) -> str:
    """An edge id in the on-disk `e-{source}--{target}` style (hyphens inside
    each endpoint become underscores, matching the seeded fixtures)."""
    return f"e-{source.replace('-', '_')}--{target.replace('-', '_')}"


def validate_node_create(body: dict[str, Any]) -> Optional[tuple[int, str, str]]:
    """Validate an add-node request body. Returns `None` when valid, else the
    `(status, code, message)` for the first rule broken, checked in this order:
    node type, then ≥1 edge, then each edge's type and a present target."""
    if body.get("node_type") not in NODE_TYPES:
        return (
            400,
            "INVALID_NODE_TYPE",
            f"node_type must be one of the seven flat types, got "
            f"{body.get('node_type')!r}",
        )
    edges = body.get("edges")
    if not isinstance(edges, list) or len(edges) == 0:
        return (
            400,
            "EDGE_REQUIRED",
            "At least one edge to an existing node is required to add a new node.",
        )
    for edge in edges:
        if not isinstance(edge, dict) or not edge.get("target_node_id"):
            return (
                400,
                "EDGE_REQUIRED",
                "Every edge row must name an existing target node.",
            )
        if edge.get("edge_type") not in EDGE_TYPES:
            return (
                400,
                "INVALID_EDGE_TYPE",
                f"edge_type must be one of the four structural types, got "
                f"{edge.get('edge_type')!r}",
            )
    return None


def add_node(
    graph: dict[str, Any], body: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Append a new node and its declared edges to `graph` in place. Returns the
    `(new_node, created_edges)`. Assumes `body` already passed
    `validate_node_create`."""
    existing = {n["id"] for n in graph.get("nodes", [])}
    node_type_by_id = {n["id"]: n.get("node_type") for n in graph.get("nodes", [])}
    node_id = make_node_id(body.get("title", "node"), existing)
    node: dict[str, Any] = {
        "id": node_id,
        "node_type": body["node_type"],
        "title": body.get("title", node_id),
        "description": body.get("description"),
        "source_url": body.get("source_url"),
    }
    if body.get("attachment_submission_id"):
        node["attachment_submission_id"] = body["attachment_submission_id"]
    graph.setdefault("nodes", []).append(node)

    created: list[dict[str, Any]] = []
    for edge in body["edges"]:
        target = edge["target_node_id"]
        # Seeded convention: a task node is always the edge SOURCE (edges read
        # task → anchor). Preserve it when the target is a task so the new
        # anchor also surfaces on the Task Screen, which lists a task's
        # OUTGOING edges only. Anchor→anchor edges keep the new node as source.
        if node_type_by_id.get(target) == "task":
            source_id, target_id = target, node_id
        else:
            source_id, target_id = node_id, target
        edge_id = make_edge_id(source_id, target_id)
        record = {
            "id": edge_id,
            "source": source_id,
            "target": target_id,
            "edge_type": edge["edge_type"],
        }
        graph.setdefault("edges", []).append(record)
        created.append(record)
    return node, created


def canned_analysis(source_id: str, target_id: str) -> Optional[list[dict[str, Any]]]:
    """The demo pair's canned, verbatim-cited findings, or `None` for any other
    pair (the route then falls back to the live finder)."""
    if frozenset({source_id, target_id}) == _DEMO_ANALYZE_PAIR:
        return [dict(f) for f in _DEMO_ANALYZE_FINDINGS]
    return None
