"""Tests for the Drafting Workspace routes.

Same shape as `test_api_review.py`: each test copies the seeded
`data/workstreams/` into `tmp_path`, so reads double as integrity checks on the
real demo fixtures while writes mutate only the throwaway copy. No network and
no credentials — the Copilot route's live call (`engine.copilot.copilot_reply`)
is injected as `copilot_reply_fn`, mirroring the `find_connections_fn` seam
`test_api_analyze_live.py` already stubs the same way.
"""

import json
import shutil

import pytest
from fastapi.testclient import TestClient

from engine import workstreams
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


def test_GET_draft_returns_the_blank_working_draft(tmp_path):
    """The demo opens on a blank page: the drafter builds the PD from scratch
    with the Copilot, so the seeded working draft ships empty."""
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/workstreams/{_OPRES}/tasks/{_TASK}/draft").json()
    assert body["node_id"] == _TASK
    assert body["content_html"] == ""
    assert body["last_saved_at"] is None


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
# The live Copilot call (`engine.copilot.copilot_reply`) is injected as
# `copilot_reply_fn`, same DI pattern `test_api_analyze_live.py` uses for
# `find_connections_fn` — no network/credentials touched here.


_UNSET = object()  # "leave the fixture alone", distinct from "remove the key"


def _rewrite_task_type(dst, task_type):
    """Set (or, with `None`, remove) `task_type` on the copied task node."""
    path = dst / _OPRES / "graph.json"
    graph = json.loads(path.read_text(encoding="utf-8"))
    node = next(n for n in graph["nodes"] if n["id"] == _TASK)
    if task_type is None:
        node.pop("task_type", None)
    else:
        node["task_type"] = task_type
    path.write_text(json.dumps(graph, indent=2), encoding="utf-8")


def _rewrite_deliverable_type(dst, deliverable_type):
    """Set (or, with `None`, remove) `deliverable_type` on the copied record.

    The record stores the human LABEL ("Exposure Draft"), not the code.
    """
    path = dst / _OPRES / "workstream.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    if deliverable_type is None:
        record.pop("deliverable_type", None)
    else:
        record["deliverable_type"] = deliverable_type
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _make_copilot_client(tmp_path, reply_fn, *, task_type=_UNSET, deliverable_type=_UNSET):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    if task_type is not _UNSET:
        _rewrite_task_type(dst, task_type)
    if deliverable_type is not _UNSET:
        _rewrite_deliverable_type(dst, deliverable_type)
    return TestClient(create_app(workstreams_dir=dst, copilot_reply_fn=reply_fn))


def _capturing_client(tmp_path, **kwargs):
    """A copilot client whose reply_fn records the kwargs the route passed it."""
    captured = {}

    def capture(**kw):
        captured.update(kw)
        return {"role": "copilot", "text": "ok"}

    return _make_copilot_client(tmp_path, capture, **kwargs), captured


def test_POST_copilot_resolves_the_intent_from_the_task_node(tmp_path):
    """The drafter is never asked: the intent is the kind already recorded on
    the working draft, and the request body never carries it."""
    client, captured = _capturing_client(tmp_path, task_type="FAQ")
    res = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot",
        json={"message": "hi"},
    )
    assert res.status_code == 200
    assert captured["intent"] == "FAQ"


def test_POST_copilot_returns_the_injected_reply(tmp_path):
    stub_reply = {"role": "copilot", "text": "Here's a redraft of §6.3."}
    client = _make_copilot_client(tmp_path, lambda **kwargs: stub_reply)
    body = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot",
        json={"message": "hi", "history": []},
    ).json()
    assert body["reply"] == stub_reply


def test_POST_copilot_passes_message_history_and_references_to_the_reply_fn(tmp_path):
    captured = {}

    def capture(**kwargs):
        captured.update(kwargs)
        return {"role": "copilot", "text": "ok"}

    client = _make_copilot_client(tmp_path, capture)
    history = [{"role": "user", "text": "hi"}, {"role": "copilot", "text": "hello"}]
    client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot",
        json={
            "message": "draft §6.3",
            "history": history,
            "referenced_finding_ids": ["e-opres_v0_3--bcbs_opres_2021~0"],
        },
    )
    assert captured["message"] == "draft §6.3"
    assert captured["history"] == history
    assert captured["referenced_finding_ids"] == ["e-opres_v0_3--bcbs_opres_2021~0"]
    assert captured["intent"] == "PD"
    assert captured["node"]["id"] == _TASK
    assert captured["workstream_id"] == _OPRES
    # No draft/selection sent → both default to None.
    assert captured["draft_text"] is None
    assert captured["selection_text"] is None


def test_POST_copilot_flattens_draft_html_and_forwards_the_selection(tmp_path):
    captured = {}

    def capture(**kwargs):
        captured.update(kwargs)
        return {"role": "copilot", "text": "ok"}

    client = _make_copilot_client(tmp_path, capture)
    client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot",
        json={
            "message": "suggestions on this?",
            "draft_html": "<h2>PART F</h2><p>This Part does <strong>not</strong> displace.</p>",
            "draft_selection": "This Part does not displace.",
        },
    )
    # HTML flattened to text: tags gone, block boundaries preserved.
    assert "PART F" in captured["draft_text"]
    assert "This Part does not displace." in captured["draft_text"]
    assert "<h2>" not in captured["draft_text"]
    assert "<strong>" not in captured["draft_text"]
    assert captured["selection_text"] == "This Part does not displace."


def test_POST_copilot_ignores_an_intent_still_sent_in_the_body(tmp_path):
    """A stale client must not get a 400 for sending a field the server no longer
    wants. The node's recorded kind wins; the body's is dropped on the floor."""
    client, captured = _capturing_client(tmp_path, task_type="DECK")
    res = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot",
        json={"intent": "BENCHMARK", "message": "hi"},
    )
    assert res.status_code == 200
    assert captured["intent"] == "DECK"


def test_POST_copilot_does_not_reject_an_intent_outside_the_vocabulary(tmp_path):
    """Nothing validates the body's `intent` any more, because nothing reads it."""
    client, captured = _capturing_client(tmp_path, task_type="ED")
    res = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot",
        json={"intent": "Freestyle", "message": "hi"},
    )
    assert res.status_code == 200
    assert captured["intent"] == "ED"


def test_POST_copilot_falls_back_to_the_workstreams_deliverable_type(tmp_path):
    """A task node predating the task-type epic carries no `task_type`, so the
    kind is read off the workstream record — which stores the LABEL ("Exposure
    Draft"), hence the reverse map to its code."""
    client, captured = _capturing_client(
        tmp_path, task_type=None, deliverable_type="Exposure Draft"
    )
    res = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot",
        json={"message": "hi"},
    )
    assert res.status_code == 200
    assert captured["intent"] == "ED"


def test_POST_copilot_falls_back_to_PD_when_nothing_is_recorded(tmp_path):
    """Neither the node nor the record has a kind: the Copilot still answers,
    framed as a policy document. It never asks, and it never errors."""
    client, captured = _capturing_client(
        tmp_path, task_type=None, deliverable_type=None
    )
    res = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot",
        json={"message": "hi"},
    )
    assert res.status_code == 200
    assert captured["intent"] == "PD"


def test_the_deleted_intent_error_code_appears_nowhere_in_the_engine():
    """The error code is deleted, not merely unreachable — grep the source so a
    re-introduction anywhere in `engine/` fails here rather than in review.

    The needle is assembled at runtime so this file is not itself an offender,
    which keeps the sweep honest: it covers every `.py` under `engine/`, tests
    included, with no exclusion list to rot.
    """
    needle = "INVALID_" + "INTENT"
    offenders = [
        str(p.relative_to(REPO_ROOT))
        for p in (REPO_ROOT / "engine").rglob("*.py")
        if needle in p.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_POST_copilot_400_for_an_empty_message(tmp_path):
    client = _make_copilot_client(tmp_path, lambda **kwargs: {"role": "copilot", "text": "x"})
    res = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot",
        json={"message": "   "},
    )
    assert res.status_code == 400
    assert res.json()["code"] == "MESSAGE_REQUIRED"


@pytest.mark.parametrize("task_type", list(workstreams.TASK_TYPES))
def test_POST_copilot_honours_every_recorded_kind(task_type: str, tmp_path):
    """Every one of the eight kinds reaches the seam as recorded — no kind is
    silently coerced to the old "Policy Document" default."""
    client, captured = _capturing_client(tmp_path, task_type=task_type)
    res = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot",
        json={"message": "hi"},
    )
    assert res.status_code == 200
    assert captured["intent"] == task_type


@pytest.mark.parametrize(
    ("workstream_id", "node_id"),
    [
        (_OPRES, _ANCHOR),
        ("open-finance-pd-2026", "bis-papers-168"),
    ],
)
def test_POST_copilot_404_when_node_is_not_a_task(workstream_id, node_id, tmp_path):
    """Dropping `intent` widened no door: an anchor node is still refused, and
    still with `TASK_NOT_FOUND` — `_task_node` uses one code for both "not a
    task" and "no such node"."""
    client = _make_copilot_client(tmp_path, lambda **kwargs: {"role": "copilot", "text": "x"})
    res = client.post(
        f"/api/workstreams/{workstream_id}/tasks/{node_id}/copilot",
        json={"message": "hi"},
    )
    assert res.status_code == 404
    assert res.json()["code"] == "TASK_NOT_FOUND"


def test_POST_copilot_502_when_the_live_call_fails(tmp_path):
    def failing(**kwargs):
        raise RuntimeError("Foundry credentials missing")

    client = _make_copilot_client(tmp_path, failing)
    res = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot",
        json={"message": "hi"},
    )
    assert res.status_code == 502
    assert res.json()["code"] == "COPILOT_FAILED"


# --- POST copilot/stream ---------------------------------------------------
# The streaming variant of the copilot route. `copilot_stream_fn` is injected
# so tests stub the generator with no network or credentials.

def _make_stream_client(tmp_path, stream_fn):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    return TestClient(create_app(workstreams_dir=dst, copilot_stream_fn=stream_fn))


def test_POST_copilot_stream_returns_sse_events(tmp_path):
    def stub_stream_fn(**kwargs):
        yield 'event: token\ndata: {"t": "Hello"}\n\n'
        yield 'event: done\ndata: {}\n\n'

    client = _make_stream_client(tmp_path, stub_stream_fn)
    res = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot/stream",
        json={"message": "hi", "history": [], "referenced_finding_ids": []},
    )
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    body = res.text
    assert "event: token" in body
    assert "event: done" in body


def test_POST_copilot_stream_resolves_the_intent_from_the_task_node(tmp_path):
    """The streaming route resolves the kind exactly as the blocking one does —
    the resolution lives in `_resolve_intent`, not in either route."""
    captured = {}

    def capture_stream(**kwargs):
        captured.update(kwargs)
        yield "event: done\ndata: {}\n\n"

    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    _rewrite_task_type(dst, "FEEDBACK")
    client = TestClient(create_app(workstreams_dir=dst, copilot_stream_fn=capture_stream))

    res = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot/stream",
        json={"message": "hi"},
    )

    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    assert captured["intent"] == "FEEDBACK"


def test_POST_copilot_stream_400_for_empty_message(tmp_path):
    client = _make_stream_client(tmp_path, lambda **kwargs: iter([]))
    res = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot/stream",
        json={"message": ""},
    )
    assert res.status_code == 400
    assert res.json()["code"] == "MESSAGE_REQUIRED"


def test_POST_copilot_stream_404_for_non_task_node(tmp_path):
    client = _make_stream_client(tmp_path, lambda **kwargs: iter([]))
    res = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_ANCHOR}/copilot/stream",
        json={"message": "hi"},
    )
    assert res.status_code == 404
    assert res.json()["code"] == "TASK_NOT_FOUND"
