"""The neighbourhood hop rule shared by the Pairwise Findings box and the
Reviewed tab.

`neighbourhood_edges` keeps an edge when at least one endpoint is the task node
or a direct neighbour of it. The interesting cases are all about what it
*excludes* (second-order ↔ second-order) and what it must not assume (edge
direction), because the two live fixtures use opposite conventions:

- `opres-v2` points its edges task → anchor,
- `open-finance-pd-2026` points them anchor → ED, i.e. INTO the shared node.

A rule that reads only `source` would return almost nothing on the second one.
"""

import json

from engine import workstreams
from engine.config import REPO_ROOT

_WS_DIR = REPO_ROOT / "data" / "workstreams"


def _edges(workstream_id: str) -> list[dict]:
    graph = json.loads(
        (_WS_DIR / workstream_id / "graph.json").read_text(encoding="utf-8")
    )
    return graph["edges"]


# --- the live demo fixture --------------------------------------------------


def test_open_finance_pulls_in_every_second_order_edge():
    """The task node has ONE edge, and all 130 findings hang off edges between
    its neighbour and other documents. Those must be in scope, or the box is
    empty on the demo workstream."""
    edges = _edges("open-finance-pd-2026")
    kept = workstreams.neighbourhood_edges(edges, "open-finance-pd-2026-pd")

    assert [e["id"] for e in kept] == [
        "e-open_finance_pd_2026_pd--ed_open_finance_2025",
        "e-hkma_open_api_framework--ed_open_finance_2025",
        "e-bis_papers_168--ed_open_finance_2025",
        "e-rmit_2025--ed_open_finance_2025",
        "e-abs_mas_api_playbook--ed_open_finance_2025",
    ]


def test_edges_pointing_into_a_neighbour_are_kept():
    """Direction independence, stated as its own assertion: every edge in this
    fixture except the task's own points INTO `ed-open-finance-2025`, so the
    task node is the edge *target* nowhere and the source only once."""
    edges = _edges("open-finance-pd-2026")
    kept = workstreams.neighbourhood_edges(edges, "open-finance-pd-2026-pd")

    inbound = [e for e in kept if e["target"] == "ed-open-finance-2025"]
    assert len(inbound) == 5  # all five, incl. the task's own
    assert all(e["source"] != "open-finance-pd-2026-pd" for e in inbound[1:])


# --- the retired task-outward fixture ---------------------------------------


def test_opres_v2_includes_edges_of_the_other_task_node():
    """`opres-v2` has a second task node (`opres-pd-v0-0`) whose edges point at
    first-order neighbours of `opres-pd-v0-3`. Those qualify: one endpoint is a
    direct neighbour. Ten of ten edges are in scope here."""
    edges = _edges("opres-v2")
    kept = workstreams.neighbourhood_edges(edges, "opres-pd-v0-3")

    assert len(kept) == 10
    ids = {e["id"] for e in kept}
    assert "e-opres_v0_0--bcbs_opres_2021" in ids
    assert "e-opres_v0_0--hkma_spm_or2" in ids
    # The IAIS paper is two hops out but its edge lands on `opres-dp-2025`,
    # a first-order neighbour, so it is in scope too.
    assert (
        "e-iais_draft_application_paper_on_operational_resilience_objectives_"
        "and_toolkit--opres_dp_2025" in ids
    )


def test_a_first_order_only_graph_is_unchanged_by_the_widening():
    """Every `opres-v2` edge touches the task or one of its neighbours, so the
    rule is a no-op there — the regression guarantee for the retired fixture."""
    edges = _edges("opres-v2")
    kept = workstreams.neighbourhood_edges(edges, "opres-pd-v0-3")
    assert [e["id"] for e in kept] == [e["id"] for e in edges]


# --- exclusion --------------------------------------------------------------


def test_second_order_to_second_order_edges_are_excluded():
    """The rule's whole point. HKMA and BIS are each two hops from the task, so
    a linkage between THEM relates neither to the draft nor to anything the
    drafter declared."""
    edges = _edges("open-finance-pd-2026") + [
        {
            "id": "e-hkma_open_api_framework--bis_papers_168",
            "source": "hkma-open-api-framework",
            "target": "bis-papers-168",
            "edge_type": "references",
        }
    ]
    kept = workstreams.neighbourhood_edges(edges, "open-finance-pd-2026-pd")

    assert len(kept) == 5
    assert "e-hkma_open_api_framework--bis_papers_168" not in {e["id"] for e in kept}


def test_a_third_order_edge_is_excluded():
    """Three hops out is excluded for the same reason, and proves the rule is
    bounded rather than transitive."""
    edges = _edges("open-finance-pd-2026") + [
        {
            "id": "e-far--further",
            "source": "hkma-open-api-framework",
            "target": "some-unrelated-doc",
            "edge_type": "references",
        },
        {
            "id": "e-further--furthest",
            "source": "some-unrelated-doc",
            "target": "another-unrelated-doc",
            "edge_type": "references",
        },
    ]
    kept = {
        e["id"]
        for e in workstreams.neighbourhood_edges(edges, "open-finance-pd-2026-pd")
    }
    assert "e-far--further" not in kept
    assert "e-further--furthest" not in kept


# --- degenerate inputs ------------------------------------------------------


def test_an_isolated_node_has_an_empty_neighbourhood():
    edges = _edges("open-finance-pd-2026")
    assert workstreams.neighbourhood_edges(edges, "not-in-this-graph") == []


def test_no_edges_at_all():
    assert workstreams.neighbourhood_edges([], "open-finance-pd-2026-pd") == []


def test_graph_order_is_preserved():
    """Callers rely on server order being graph order — the frontend does all
    grouping and sorting, and the engine never reorders findings."""
    edges = _edges("open-finance-pd-2026")
    kept = workstreams.neighbourhood_edges(edges, "open-finance-pd-2026-pd")
    positions = [edges.index(e) for e in kept]
    assert positions == sorted(positions)


def test_each_edge_appears_once():
    """An edge with BOTH endpoints in the neighbourhood must not be emitted
    twice — the task's own edge is exactly that case."""
    edges = _edges("open-finance-pd-2026")
    kept = workstreams.neighbourhood_edges(edges, "open-finance-pd-2026-pd")
    ids = [e["id"] for e in kept]
    assert len(ids) == len(set(ids))


def test_it_is_a_superset_of_the_task_s_own_edges():
    """Whatever else changes, every edge the old task-screen scan found must
    still be found."""
    edges = _edges("opres-v2")
    task_own = [e["id"] for e in edges if e.get("source") == "opres-pd-v0-3"]
    kept = {e["id"] for e in workstreams.neighbourhood_edges(edges, "opres-pd-v0-3")}
    assert set(task_own) <= kept
