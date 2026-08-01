"""The Pairwise Findings route — every finding in a task's neighbourhood.

Same fixture discipline as `test_api_drafting.py`: each test copies the seeded
`data/workstreams/` into `tmp_path`, so reads double as integrity checks on the
real demo fixtures while writes touch only the throwaway copy.

`open-finance-pd-2026` is the fixture that matters here. Its task node has ONE
edge and that pair has no findings file at all, while 130 findings hang off
edges between its neighbour and other documents. The old task-screen scan
(`source == node_id`) sees none of them, which is the defect this route fixes.
"""

import json
import shutil

from fastapi.testclient import TestClient

from engine.api import create_app
from engine.config import REPO_ROOT

_WS = "open-finance-pd-2026"
_TASK = "open-finance-pd-2026-pd"
_ANCHOR = "rmit-2025"  # a real node, but not a task

_ED = "ed-open-finance-2025"
_RMIT_EDGE = "e-rmit_2025--ed_open_finance_2025"
_HKMA_EDGE = "e-hkma_open_api_framework--ed_open_finance_2025"
_BIS_EDGE = "e-bis_papers_168--ed_open_finance_2025"
_TASK_EDGE = "e-open_finance_pd_2026_pd--ed_open_finance_2025"
_ABS_EDGE = "e-abs_mas_api_playbook--ed_open_finance_2025"

_OPRES = "opres-v2"
_OPRES_TASK = "opres-pd-v0-3"

def _scrub_demo_state(workstreams_dir) -> None:
    """Reset the copied fixture to a pristine review state.

    The demo workstream is BUILD-AND-PERSIST (see CLAUDE.md): its committed
    findings carry real `review_state` values and it ships a generated
    `recommendations/` set, so the demo needs no model call on the day. That is
    deliberate data, not test scaffolding — but it means a test asserting "an
    untouched fixture" is really asserting "whatever the demo happens to hold
    today", which breaks the moment a drafter accepts one more finding.

    So every test here starts from an explicitly pristine copy and creates the
    acceptances it needs. Scrubbing the tmp copy only; the tracked fixture is
    never touched.
    """
    for path in (workstreams_dir).rglob("findings/*.json"):
        findings_list = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for finding in findings_list:
            if finding.pop("review_state", None) is not None:
                changed = True
        if changed:
            path.write_text(
                json.dumps(findings_list, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
    for path in (workstreams_dir).rglob("recommendations/*.json"):
        path.unlink()
    # Guardrails too: a saved set replaces the shipped defaults, so a leftover
    # would silently change what the generation prompt contains.
    for path in (workstreams_dir).glob("*/guardrails.json"):
        path.unlink()


def _make_client(tmp_path):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    _scrub_demo_state(dst)
    return TestClient(create_app(workstreams_dir=dst)), dst


def _get(client, workstream=_WS, node=_TASK):
    return client.get(f"/api/workstreams/{workstream}/tasks/{node}/pairwise-findings")


def _finding_id(client, edge_id, index, workstream=_WS) -> str:
    """The real id of the nth finding on an edge.

    Ids are NOT uniformly derived: `engine.findings.load` only synthesises
    `{edge_id}~{i}` when a finding carries no `id` of its own, and the
    `open-finance-*` fixtures ship explicit opaque ids (`4f9f91c02ef5`) while
    `opres-v2` and `_cross` ship none. Reading the id back is the only way that
    works for both.
    """
    body = client.get(f"/api/workstreams/{workstream}/edges/{edge_id}/review").json()
    return body["findings"][index]["id"]


def _set_state(client, edge_id, index, state, workstream=_WS):
    finding_id = _finding_id(client, edge_id, index, workstream)
    res = client.patch(
        f"/api/workstreams/{workstream}/edges/{edge_id}/findings/{finding_id}",
        json={"review_state": state},
    )
    assert res.status_code == 200, res.text
    return finding_id


# --- scope: the whole point -------------------------------------------------


def test_second_order_findings_are_surfaced(tmp_path):
    """The regression guard for the whole story. The task's only edge is
    unanalysed, so the old per-neighbour scan returns zero findings here."""
    client, _ = _make_client(tmp_path)
    body = _get(client).json()

    assert body["counts"]["total"] == 130
    assert len(body["findings"]) == 130
    assert {f["edge_id"] for f in body["findings"]} == {
        _RMIT_EDGE,
        _HKMA_EDGE,
        _BIS_EDGE,
    }


def test_label_counts_match_the_fixture(tmp_path):
    """All five labels always present, including `conflicts-with` at zero — the
    frontend must never have to synthesise a missing group."""
    client, _ = _make_client(tmp_path)
    body = _get(client).json()

    assert body["counts"]["by_label"] == {
        "conflicts-with": {"total": 0, "pending": 0},
        "differs-on": {"total": 30, "pending": 30},
        "silent-on": {"total": 14, "pending": 14},
        "goes-beyond": {"total": 11, "pending": 11},
        "aligns-with": {"total": 75, "pending": 75},
    }


def test_second_order_to_second_order_edges_are_excluded(tmp_path):
    """A linkage between two documents that are each two hops out must not
    appear. Written against the tmp copy — the tracked fixture is untouched."""
    client, ws_dir = _make_client(tmp_path)
    graph_path = ws_dir / _WS / "graph.json"
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    graph["edges"].append(
        {
            "id": "e-hkma--bis",
            "source": "hkma-open-api-framework",
            "target": "bis-papers-168",
            "edge_type": "references",
        }
    )
    graph_path.write_text(json.dumps(graph), encoding="utf-8")
    (ws_dir / _WS / "findings" / "e-hkma--bis.json").write_text(
        json.dumps(
            [
                {
                    "summary": "Invented linkage that must not surface.",
                    "label": "conflicts-with",
                    "sentiment": None,
                    "source_clauses": [{"clause_number": "HKMA 1.1", "text": "x"}],
                    "target_clauses": [{"clause_number": "BIS 1.1", "text": "y"}],
                }
            ]
        ),
        encoding="utf-8",
    )

    body = _get(client).json()
    assert body["counts"]["total"] == 130
    assert body["counts"]["by_label"]["conflicts-with"]["total"] == 0
    assert "e-hkma--bis" not in {f["edge_id"] for f in body["findings"]}


# --- coverage ---------------------------------------------------------------


def test_unanalysed_pairs_are_listed_in_graph_order(tmp_path):
    client, _ = _make_client(tmp_path)
    body = _get(client).json()

    assert [p["edge_id"] for p in body["unanalysed_pairs"]] == [
        _TASK_EDGE,
        _ABS_EDGE,
    ]
    assert body["counts"]["analysed_pairs"] == 3
    assert body["counts"]["total_pairs"] == 5


def test_an_unanalysed_pair_carries_both_endpoints(tmp_path):
    """The coverage strip has to name the pair, so both ends travel."""
    client, _ = _make_client(tmp_path)
    pair = next(
        p for p in _get(client).json()["unanalysed_pairs"] if p["edge_id"] == _ABS_EDGE
    )
    assert pair["left"]["id"] == "abs-mas-api-playbook"
    assert pair["right"]["id"] == _ED
    assert pair["left"]["title"] == "ABS-MAS API Playbook"
    assert pair["edge_type"] == "references"


# --- the filter's node list -------------------------------------------------


def test_filter_nodes_cover_the_neighbourhood_excluding_the_task(tmp_path):
    client, _ = _make_client(tmp_path)
    nodes = _get(client).json()["nodes"]

    assert [n["id"] for n in nodes] == [
        _ED,
        "hkma-open-api-framework",
        "bis-papers-168",
        "rmit-2025",
        "abs-mas-api-playbook",
    ]
    assert _TASK not in {n["id"] for n in nodes}


def test_filter_nodes_carry_their_findings_count(tmp_path):
    """A node whose pair has never been analysed still gets a chip, at zero."""
    client, _ = _make_client(tmp_path)
    counts = {n["id"]: n["findings_count"] for n in _get(client).json()["nodes"]}

    assert counts["rmit-2025"] == 51
    assert counts["hkma-open-api-framework"] == 47
    assert counts["bis-papers-168"] == 32
    assert counts["abs-mas-api-playbook"] == 0
    # The ED node sits on every analysed edge, so it carries their sum.
    assert counts[_ED] == 130


# --- review state -----------------------------------------------------------


def test_review_state_rides_on_the_card(tmp_path):
    client, _ = _make_client(tmp_path)
    accepted = _set_state(client, _RMIT_EDGE, 0, "accepted")

    body = _get(client).json()
    card = next(f for f in body["findings"] if f["id"] == accepted)
    assert card["review_state"] == "accepted"
    # The total is stable; only pending moves.
    assert body["counts"]["by_label"]["aligns-with"] == {"total": 75, "pending": 74}
    assert body["counts"]["total"] == 130


def test_dismissed_findings_still_appear(tmp_path):
    """Unlike the Reviewed tab, this box shows every finding whatever its state —
    dismissed cards sink in the UI rather than vanishing."""
    client, _ = _make_client(tmp_path)
    dismissed = _set_state(client, _RMIT_EDGE, 1, "dismissed")

    body = _get(client).json()
    card = next(f for f in body["findings"] if f["id"] == dismissed)
    assert card["review_state"] == "dismissed"
    assert body["counts"]["total"] == 130


def test_pending_is_the_default_for_an_untouched_fixture(tmp_path):
    client, _ = _make_client(tmp_path)
    body = _get(client).json()
    assert all(f["review_state"] == "pending" for f in body["findings"])


# --- card shape -------------------------------------------------------------


def test_a_card_carries_clause_numbers_but_no_clause_text(tmp_path):
    """The verbatim guarantee: nothing on a card can misquote, because no card
    quotes. Text lives on the review route, sourced from the finding itself."""
    client, _ = _make_client(tmp_path)
    card = next(
        f for f in _get(client).json()["findings"] if f["edge_id"] == _RMIT_EDGE
    )

    assert card["source_clause_number"]
    assert card["target_clause_number"]
    assert "source_clauses" not in card
    assert "target_clauses" not in card
    assert card["summary"]


def test_endpoints_are_not_normalised_to_put_the_task_first(tmp_path):
    """`open-finance-pd-2026` points its edges INTO the ED node. `left`/`right`
    stay `source`/`target` so the UI can name the pair as stored."""
    client, _ = _make_client(tmp_path)
    card = next(
        f for f in _get(client).json()["findings"] if f["edge_id"] == _RMIT_EDGE
    )

    assert card["left"]["id"] == "rmit-2025"
    assert card["right"]["id"] == _ED
    assert card["left"]["node_type"] == "internal-published"


# --- the draft is never a gate ----------------------------------------------


def test_draft_content_does_not_change_the_response(tmp_path):
    client, _ = _make_client(tmp_path)
    before = _get(client).json()

    res = client.put(
        f"/api/workstreams/{_WS}/tasks/{_TASK}/draft",
        json={"content_html": "<p>1.1 Scope of this policy document.</p>"},
    )
    assert res.status_code == 200

    assert _get(client).json() == before


# --- the retired task-outward fixture ---------------------------------------


def test_opres_v2_still_works_and_widens(tmp_path):
    """The retired fixture keeps working. Its scope is wider than the task's own
    edges: the second task node's edges qualify because their targets are
    first-order neighbours of `opres-pd-v0-3`."""
    client, _ = _make_client(tmp_path)
    body = _get(client, workstream=_OPRES, node=_OPRES_TASK).json()

    assert body["counts"]["total"] == 6
    assert body["counts"]["analysed_pairs"] == 4
    assert body["counts"]["total_pairs"] == 10
    assert len(body["nodes"]) == 9
    # A second task node is a legitimate neighbourhood document and gets a chip.
    assert "opres-pd-v0-0" in {n["id"] for n in body["nodes"]}
    assert _OPRES_TASK not in {n["id"] for n in body["nodes"]}


# --- guards -----------------------------------------------------------------


def test_unknown_workstream_404s(tmp_path):
    client, _ = _make_client(tmp_path)
    res = _get(client, workstream="nope", node="x")
    assert res.status_code == 404
    assert res.json()["code"] == "WORKSTREAM_NOT_FOUND"


def test_unknown_node_404s(tmp_path):
    client, _ = _make_client(tmp_path)
    res = _get(client, node="not-a-real-node")
    assert res.status_code == 404
    assert res.json()["code"] == "NODE_NOT_FOUND"


def test_a_non_task_node_400s(tmp_path):
    client, _ = _make_client(tmp_path)
    res = _get(client, node=_ANCHOR)
    assert res.status_code == 400
    assert res.json()["code"] == "NOT_A_TASK"


# --- idempotency ------------------------------------------------------------


def test_accepting_twice_is_a_no_op(tmp_path):
    client, ws_dir = _make_client(tmp_path)
    _set_state(client, _RMIT_EDGE, 0, "accepted")
    first = (ws_dir / _WS / "findings" / f"{_RMIT_EDGE}.json").read_text(
        encoding="utf-8"
    )
    _set_state(client, _RMIT_EDGE, 0, "accepted")
    second = (ws_dir / _WS / "findings" / f"{_RMIT_EDGE}.json").read_text(
        encoding="utf-8"
    )

    assert first == second
    body = _get(client).json()
    assert body["counts"]["by_label"]["aligns-with"] == {"total": 75, "pending": 74}
