"""Tests for the Drafting Workspace routes.

Same shape as `test_api_review.py`: each test copies the seeded
`data/workstreams/` into `tmp_path`, so reads double as integrity checks on the
real demo fixtures while writes mutate only the throwaway copy. No network and no
credentials — the Copilot is a scripted map, not a model.
"""

import json
import shutil

import pytest
from fastapi.testclient import TestClient

from engine import copilot_scripts
from engine.api import create_app
from engine.config import REPO_ROOT

_OPRES = "opres-v2"
_TASK = "opres-pd-v0-3"
_ANCHOR = "bcbs-opres-2021"  # a real node, but not a task
_BCBS_EDGE = "e-opres_v0_3--bcbs_opres_2021"


def _make_client(tmp_path):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    return TestClient(create_app(workstreams_dir=dst)), dst


def _accept_first_bcbs_finding(client) -> str:
    """Accept one finding so the Reviewed tab has something to return.

    The fixtures ship every finding `pending` on purpose — the demo earns its
    accepted linkages by walking the review screen — so a Reviewed-tab test has
    to create the state it asserts on.
    """
    finding_id = f"{_BCBS_EDGE}~0"
    res = client.patch(
        f"/api/workstreams/{_OPRES}/edges/{_BCBS_EDGE}/findings/{finding_id}",
        json={"review_state": "accepted"},
    )
    assert res.status_code == 200
    return finding_id


# --- GET reviewed-linkages -------------------------------------------------


def test_GET_reviewed_linkages_is_empty_before_anything_is_accepted(tmp_path):
    """Fixture integrity: nothing ships pre-accepted."""
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/workstreams/{_OPRES}/tasks/{_TASK}/reviewed-linkages").json()
    assert body["findings"] == []


def test_GET_reviewed_linkages_returns_only_accepted_findings(tmp_path):
    client, _ = _make_client(tmp_path)
    accepted_id = _accept_first_bcbs_finding(client)

    body = client.get(f"/api/workstreams/{_OPRES}/tasks/{_TASK}/reviewed-linkages").json()

    assert [f["id"] for f in body["findings"]] == [accepted_id]
    card = body["findings"][0]
    assert card["label"] == "aligns-with"
    assert card["edge_id"] == _BCBS_EDGE
    assert card["right"]["title"] == "BCBS OpRes 2021"
    assert card["source_clause_number"] == "OpRes PD 4.4"


def test_GET_reviewed_linkages_excludes_dismissed(tmp_path):
    client, _ = _make_client(tmp_path)
    _accept_first_bcbs_finding(client)
    client.patch(
        f"/api/workstreams/{_OPRES}/edges/{_BCBS_EDGE}/findings/{_BCBS_EDGE}~1",
        json={"review_state": "dismissed"},
    )

    body = client.get(f"/api/workstreams/{_OPRES}/tasks/{_TASK}/reviewed-linkages").json()

    states = [f["id"] for f in body["findings"]]
    assert f"{_BCBS_EDGE}~1" not in states
    assert len(body["findings"]) == 1


def test_GET_reviewed_linkages_aggregates_across_edges(tmp_path):
    """Accepted findings on different anchors land in one list."""
    client, _ = _make_client(tmp_path)
    _accept_first_bcbs_finding(client)
    hkma_edge = "e-opres_v0_3--hkma_spm_or2"
    client.patch(
        f"/api/workstreams/{_OPRES}/edges/{hkma_edge}/findings/{hkma_edge}~0",
        json={"review_state": "accepted"},
    )

    body = client.get(f"/api/workstreams/{_OPRES}/tasks/{_TASK}/reviewed-linkages").json()

    assert {f["edge_id"] for f in body["findings"]} == {_BCBS_EDGE, hkma_edge}
    differs = next(f for f in body["findings"] if f["edge_id"] == hkma_edge)
    assert differs["label"] == "differs-on"
    assert differs["sentiment"] == "tighten"


def test_GET_reviewed_linkages_cards_carry_clause_numbers_but_never_clause_text(tmp_path):
    """The cards are references, not citations — so they cannot misquote."""
    client, _ = _make_client(tmp_path)
    _accept_first_bcbs_finding(client)
    body = client.get(f"/api/workstreams/{_OPRES}/tasks/{_TASK}/reviewed-linkages").json()
    card = body["findings"][0]
    assert "source_clauses" not in card
    assert "text" not in json.dumps(card)


def test_GET_reviewed_linkages_404_when_node_is_not_a_task(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.get(f"/api/workstreams/{_OPRES}/tasks/{_ANCHOR}/reviewed-linkages")
    assert res.status_code == 404
    assert res.json()["code"] == "TASK_NOT_FOUND"


def test_GET_reviewed_linkages_404_when_workstream_unknown(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.get(f"/api/workstreams/nope/tasks/{_TASK}/reviewed-linkages")
    assert res.status_code == 404
    assert res.json()["code"] == "WORKSTREAM_NOT_FOUND"


# --- GET related-linkages --------------------------------------------------


def test_GET_related_linkages_is_empty_on_the_seeded_fixture(tmp_path):
    """opres-v2 has no anchor↔anchor edges, so there is honestly nothing to show.

    Pinned deliberately: the alternative to an empty tab was inventing clause
    text for documents this repo has no source for.
    """
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/workstreams/{_OPRES}/tasks/{_TASK}/related-linkages").json()
    assert body["findings"] == []


def test_GET_related_linkages_returns_neighbour_pair_findings_and_excludes_task_edges(
    tmp_path,
):
    """The traversal itself, proved on a synthetic graph.

    The seeded fixture cannot exercise this (no anchor↔anchor edges), so the
    edges and findings are built here. Test-local data invents no citation: it
    never renders, and its clause text is nonsense on purpose.
    """
    client, dst = _make_client(tmp_path)
    graph_path = dst / _OPRES / "graph.json"
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    peer_edge = "e-hkma_spm_or2--bcbs_opres_2021"
    graph["edges"].append(
        {
            "id": peer_edge,
            "source": "hkma-spm-or2",
            "target": _ANCHOR,
            "edge_type": "references",
        }
    )
    graph_path.write_text(json.dumps(graph), encoding="utf-8")
    (dst / _OPRES / "findings" / f"{peer_edge}.json").write_text(
        json.dumps(
            [
                {
                    "summary": "synthetic peer linkage",
                    "label": "aligns-with",
                    "sentiment": None,
                    "source_clauses": [{"clause_number": "X 1.1", "text": "lorem"}],
                    "target_clauses": [{"clause_number": "Y 2.2", "text": "ipsum"}],
                }
            ]
        ),
        encoding="utf-8",
    )

    body = client.get(f"/api/workstreams/{_OPRES}/tasks/{_TASK}/related-linkages").json()

    assert len(body["findings"]) == 1
    card = body["findings"][0]
    assert card["edge_id"] == peer_edge
    assert card["left"]["id"] == "hkma-spm-or2"
    assert card["right"]["id"] == _ANCHOR
    # The task's own analysed edges must not leak into the peer feed.
    assert all(_TASK not in (c["left"]["id"], c["right"]["id"]) for c in body["findings"])


def test_GET_related_linkages_hops_2_is_rejected(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.get(f"/api/workstreams/{_OPRES}/tasks/{_TASK}/related-linkages?hops=2")
    assert res.status_code == 400
    assert res.json()["code"] == "HOPS_OUT_OF_RANGE"


def test_GET_related_linkages_404_when_node_is_not_a_task(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.get(f"/api/workstreams/{_OPRES}/tasks/{_ANCHOR}/related-linkages")
    assert res.status_code == 404
    assert res.json()["code"] == "TASK_NOT_FOUND"


# --- GET / PUT draft -------------------------------------------------------


def test_GET_draft_returns_the_seeded_working_draft(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/workstreams/{_OPRES}/tasks/{_TASK}/draft").json()
    assert body["node_id"] == _TASK
    assert "<strong>5.3</strong>" in body["content_html"]
    assert body["last_saved_at"] == "2026-07-13T14:30:00Z"


def test_GET_draft_clauses_are_verbatim_from_the_findings_fixtures(tmp_path):
    """The draft body quotes the same OpRes text the findings cite.

    If the two drift, the review screen and the editor would show different words
    for the same clause number — and one of them would be wrong.
    """
    client, dst = _make_client(tmp_path)
    html = client.get(f"/api/workstreams/{_OPRES}/tasks/{_TASK}/draft").json()["content_html"]
    findings = json.loads(
        (dst / _OPRES / "findings" / "e-opres_v0_3--hkma_spm_or2.json").read_text(
            encoding="utf-8"
        )
    )
    clause_text = findings[0]["source_clauses"][0]["text"]
    assert clause_text in html


def test_GET_draft_is_blank_not_404_for_a_task_never_drafted(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/workstreams/{_OPRES}/tasks/opres-pd-v0-0/draft").json()
    assert body["content_html"] == ""
    assert body["last_saved_at"] is None


def test_PUT_draft_round_trips_and_persists(tmp_path):
    client, dst = _make_client(tmp_path)
    res = client.put(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/draft",
        json={"content_html": "<h1>Edited</h1><p>New body.</p>"},
    )
    assert res.status_code == 200
    assert res.json()["content_html"] == "<h1>Edited</h1><p>New body.</p>"
    assert res.json()["last_saved_at"] is not None

    on_disk = json.loads(
        (dst / _OPRES / "drafts" / f"{_TASK}.json").read_text(encoding="utf-8")
    )
    assert on_disk["content_html"] == "<h1>Edited</h1><p>New body.</p>"


def test_PUT_draft_strips_script_tags(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.put(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/draft",
        json={"content_html": "<p>Keep</p><script>alert('xss')</script>"},
    ).json()
    assert "<script>" not in body["content_html"]
    assert "alert" not in body["content_html"]
    assert "<p>Keep</p>" in body["content_html"]


def test_PUT_draft_strips_inline_event_handlers(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.put(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/draft",
        json={"content_html": "<p onclick=\"steal()\">Text</p>"},
    ).json()
    assert "onclick" not in body["content_html"]
    assert "Text" in body["content_html"]


def test_PUT_draft_strips_javascript_urls(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.put(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/draft",
        json={"content_html": '<p><a href="javascript:steal()">click</a></p>'},
    ).json()
    assert "javascript:" not in body["content_html"]


def test_PUT_draft_keeps_the_copilot_snippet_class(tmp_path):
    """Provenance marking survives sanitization, or a drafter loses the only
    signal distinguishing generated text from their own."""
    client, _ = _make_client(tmp_path)
    body = client.put(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/draft",
        json={"content_html": "<div class=\"copilot-snippet\"><p>Generated</p></div>"},
    ).json()
    assert 'class="copilot-snippet"' in body["content_html"]


def test_PUT_draft_413_when_over_200kb(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.put(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/draft",
        json={"content_html": "<p>" + ("x" * 205_000) + "</p>"},
    )
    assert res.status_code == 413
    assert res.json()["code"] == "DRAFT_TOO_LARGE"


def test_PUT_draft_sizes_the_sanitized_payload_not_the_raw_one(tmp_path):
    """A big blob of markup we strip should clean down, not 413."""
    client, _ = _make_client(tmp_path)
    res = client.put(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/draft",
        json={"content_html": "<p>ok</p>" + "<script>" + ("x" * 205_000) + "</script>"},
    )
    assert res.status_code == 200
    assert res.json()["content_html"] == "<p>ok</p>"


def test_PUT_draft_400_when_nothing_survives_sanitization(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.put(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/draft",
        json={"content_html": "<script>alert(1)</script>"},
    )
    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_HTML"


def test_PUT_draft_allows_clearing_to_empty(tmp_path):
    """An empty payload is a legitimate clear, not a rejected one."""
    client, _ = _make_client(tmp_path)
    res = client.put(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/draft", json={"content_html": ""}
    )
    assert res.status_code == 200
    assert res.json()["content_html"] == ""


def test_PUT_draft_404_when_node_is_not_a_task(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.put(
        f"/api/workstreams/{_OPRES}/tasks/{_ANCHOR}/draft",
        json={"content_html": "<p>x</p>"},
    )
    assert res.status_code == 404
    assert res.json()["code"] == "TASK_NOT_FOUND"


def test_PUT_draft_does_not_touch_the_committed_fixture(tmp_path):
    """The tmp copy absorbs the write; the real fixture stays put."""
    client, _ = _make_client(tmp_path)
    client.put(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/draft",
        json={"content_html": "<p>scratch</p>"},
    )
    real = json.loads(
        (
            REPO_ROOT / "data" / "workstreams" / _OPRES / "drafts" / f"{_TASK}.json"
        ).read_text(encoding="utf-8")
    )
    assert "scratch" not in real["content_html"]


# --- POST copilot ----------------------------------------------------------


def test_POST_copilot_returns_the_scripted_PD_welcome(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot",
        json={"intent": "PD", "message": "hi", "turn": 0},
    ).json()
    assert body["reply"]["role"] == "copilot"
    assert "§6.3" in body["reply"]["text"]


def test_POST_copilot_second_turn_returns_the_cited_snippet(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot",
        json={"intent": "PD", "message": "yes", "turn": 1},
    ).json()
    reply = body["reply"]
    assert "<strong>6.3</strong>" in reply["snippet_html"]
    assert reply["citations"][0]["clause_number"] == "RMiT 9.4"
    assert reply["citations"][0]["text"] == copilot_scripts.RMIT_9_4_QUOTE


def test_POST_copilot_400_for_an_intent_outside_the_seven(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot",
        json={"intent": "Freestyle", "message": "hi"},
    )
    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_INTENT"


@pytest.mark.parametrize("intent", copilot_scripts.INTENTS)
def test_POST_copilot_answers_every_preset(intent: str, tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot",
        json={"intent": intent, "message": "hi"},
    )
    assert res.status_code == 200
    assert res.json()["reply"]["text"]


def test_POST_copilot_404_when_node_is_not_a_task(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_ANCHOR}/copilot",
        json={"intent": "PD", "message": "hi"},
    )
    assert res.status_code == 404
    assert res.json()["code"] == "TASK_NOT_FOUND"
