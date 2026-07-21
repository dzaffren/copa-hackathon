"""Derive node concept metadata offline — `pursuant_to` + the Concepts panel.

Product feedback asked for an "ISMP Classification" badge, a "Pursuant to:
<Act>" badge, and a Concepts disclosure (`policy_owner`, `applicability`,
`empowerment_framework`, `requirement`, `issuance_date`, `effective_date`,
`keywords`). The frontend has always rendered all of these
(`NodeDetailPanel.tsx`); nothing ever populated them, so they were dead code.

This script is the offline enrichment step, run once against the committed
fixtures (the same "offline script -> fixture -> API projection" pattern as
`scripts/project_cross_workstream_findings.py`) — no live model call, no
per-request cost. Every field it writes is either:

  - a value already carried structurally on the node (`owner` -> policy_owner), or
  - a verbatim quote from a clause the node's own document contains, resolved
    through an existing, *supported* finding — never invented.

A field this script cannot honestly derive is left absent/`null`, not
guessed. `ismp_classification` is the clearest example: no taxonomy for it
exists anywhere in this repo (the product brief only ever mocked one example
value), so this script does not write it at all — the API route continues to
report it as `null` until a real source (e.g. CAS's RH publication form) is
available. Fabricating category values would violate the verbatim-citation
product rule just as much as inventing a clause would.

Run:
    PYTHONPATH=. python scripts/enrich_node_metadata.py
"""

import json
from pathlib import Path
from typing import Any, Optional

from engine import concepts, findings
from engine.config import REPO_ROOT

WORKSTREAMS_DIR = REPO_ROOT / "data" / "workstreams"
CROSS_STORE = "_cross"


def _load_graph(workstream_dir: Path) -> Optional[dict[str, Any]]:
    graph_path = workstream_dir / "graph.json"
    if not graph_path.exists():
        return None
    return json.loads(graph_path.read_text(encoding="utf-8"))


def _save_graph(workstream_dir: Path, graph: dict[str, Any]) -> None:
    (workstream_dir / "graph.json").write_text(
        json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _pursuant_to_and_empowerment(
    workstreams_dir: Path,
    workstream_id: str,
    node: dict[str, Any],
    edges: list[dict[str, Any]],
    nodes_by_id: dict[str, dict[str, Any]],
) -> tuple[Optional[str], Optional[str]]:
    """A node's statutory basis, derived from its own `references` edge to an
    `act-law` node backed by a supported finding — never from anywhere else.

    Returns (pursuant_to, empowerment_framework): the cited act's title, and
    the node's own document quoted verbatim stating that basis. Either or both
    are `None` when no such edge/finding exists.
    """
    for edge in edges:
        if edge.get("source") != node["id"] or edge.get("edge_type") != "references":
            continue
        target = nodes_by_id.get(edge["target"])
        if target is None or target.get("node_type") != "act-law":
            continue
        try:
            edge_findings = findings.load(workstreams_dir, workstream_id, edge["id"])
        except findings.FindingsNotAnalysedError:
            continue
        for finding in edge_findings:
            if not finding.get("supported"):
                continue
            source_clauses = finding.get("source_clauses") or []
            if not source_clauses:
                continue
            return target.get("title"), source_clauses[0].get("text")
    return None, None


def _enrich_workstream(workstreams_dir: Path, workstream_id: str) -> int:
    workstream_dir = workstreams_dir / workstream_id
    graph = _load_graph(workstream_dir)
    if graph is None:
        return 0

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    nodes_by_id = {n["id"]: n for n in nodes}

    enriched = 0
    graph_changed = False
    for node in nodes:
        owner = node.get("owner") or {}
        policy_owner = owner.get("name")

        pursuant_to, empowerment_framework = _pursuant_to_and_empowerment(
            workstreams_dir, workstream_id, node, edges, nodes_by_id
        )

        if pursuant_to is not None and node.get("pursuant_to") != pursuant_to:
            node["pursuant_to"] = pursuant_to
            graph_changed = True

        if policy_owner is None and empowerment_framework is None:
            continue  # nothing to write — leave this node un-enriched

        concepts.save_concepts(
            workstreams_dir,
            workstream_id,
            node["id"],
            {
                "policy_owner": policy_owner,
                "empowerment_framework": empowerment_framework,
            },
        )
        enriched += 1

    if graph_changed:
        _save_graph(workstream_dir, graph)

    return enriched


def main() -> None:
    total = 0
    for entry in sorted(WORKSTREAMS_DIR.iterdir()):
        if not entry.is_dir() or entry.name == CROSS_STORE:
            continue
        if not (entry / "workstream.json").exists():
            continue
        count = _enrich_workstream(WORKSTREAMS_DIR, entry.name)
        if count:
            print(f"{entry.name}: enriched {count} node(s)")
        total += count
    print(f"total: {total} node(s) enriched across {WORKSTREAMS_DIR}")


if __name__ == "__main__":
    main()
