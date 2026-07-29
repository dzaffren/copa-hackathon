"""Tests for POST /api/workstreams and GET /api/reviewers.

Unlike every other route in this service, create WRITES a new directory. Tests
point `workstreams_dir` at `tmp_path` so nothing lands in the real fixture
store, and a guard test asserts the committed store is untouched.
"""

import json
import shutil

import pytest
from fastapi.testclient import TestClient

from engine import directory, workstreams
from engine.api import create_app
from engine.config import REPO_ROOT

VALID = {
    "name": "Climate Risk PD v2 · 2026",
    "description": "Response to BCBS climate principles — draft PD targeting Q4 2026.",
    "deliverable_type": "PD",
    "target_publication": "Q4 2026",
    "reviewer_ids": ["fm", "ps"],
    "access": "team_only",
}


def _make_client(tmp_path):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    return TestClient(create_app(workstreams_dir=dst)), dst


def _create(client, **overrides):
    body = {**VALID, **overrides}
    for k, v in list(body.items()):
        if v is _OMIT:
            del body[k]
    return client.post("/api/workstreams", json=body)


class _Omit:
    pass


_OMIT = _Omit()


# --- The shared deliverable vocabulary -------------------------------------


def test_task_types_are_the_eight_kinds_in_order():
    """Order is contractual: the frontend renders the dropdown in map order, so
    the drafter always meets PD first and Others last."""
    assert list(workstreams.TASK_TYPES.items()) == [
        ("PD", "Policy Document"),
        ("DP", "Discussion Paper"),
        ("ED", "Exposure Draft"),
        ("FAQ", "FAQ"),
        ("DECK", "Engagement Deck"),
        ("FEEDBACK", "Feedback Template for Industry"),
        ("BENCHMARK", "Peer Benchmarking"),
        ("OTHERS", "Others"),
    ]


@pytest.mark.parametrize(
    "label, expected",
    [
        ("Policy Document", "PD"),
        ("Feedback Template for Industry", "FEEDBACK"),
        ("Others", "OTHERS"),
        ("Nonsense", None),
        ("Other", None),
        (None, None),
    ],
)
def test_task_type_code_for_label_reverses_the_map(label, expected):
    """workstream.json stores the label, graph nodes the code, so something has
    to map back — derived from TASK_TYPES so the two directions cannot drift."""
    assert workstreams.task_type_code_for_label(label) == expected


# --- GET /api/reviewers ----------------------------------------------------


def test_GET_reviewers_excludes_the_owner(tmp_path):
    """A drafter cannot nominate themselves — enforced by the API, not the UI."""
    client, _ = _make_client(tmp_path)
    body = client.get("/api/reviewers").json()
    ids = [r["id"] for r in body["reviewers"]]
    assert directory.OWNER_ID not in ids
    assert ids == ["fm", "ps", "jn"]


# --- POST /api/workstreams -------------------------------------------------


def test_POST_creates_a_workstream_and_returns_201(tmp_path):
    client, _ = _make_client(tmp_path)
    res = _create(client)
    assert res.status_code == 201
    body = res.json()
    assert body["id"] == "climate-risk-pd-v2-2026"
    assert body["name"] == "Climate Risk PD v2 · 2026"
    assert body["owner"] == {"id": "ar", "name": "Aisyah R."}
    assert [r["id"] for r in body["reviewers"]] == ["fm", "ps"]
    assert body["access"] == "team_only"
    assert body["created_at"].endswith("Z")


def test_POST_writes_workstream_json_and_seeds_one_focal_task_node(tmp_path):
    """The graph must exist (every read path treats a missing graph.json as
    WORKSTREAM_NOT_FOUND) and now opens with exactly one focal task node so the
    first added document has an anchor to connect to."""
    client, dst = _make_client(tmp_path)
    ws_id = _create(client).json()["id"]

    meta = json.loads((dst / ws_id / "workstream.json").read_text(encoding="utf-8"))
    graph = json.loads((dst / ws_id / "graph.json").read_text(encoding="utf-8"))
    assert meta["name"] == VALID["name"]
    assert len(graph["nodes"]) == 1
    assert graph["nodes"][0]["node_type"] == "task"
    assert graph["edges"] == []
    assert meta["primary_task_id"] == graph["nodes"][0]["id"]


def test_POST_new_workstream_is_immediately_loadable_by_the_graph_route(tmp_path):
    """The round trip the form actually performs: create, then land on it —
    now centred on the seeded focal node."""
    client, _ = _make_client(tmp_path)
    ws_id = _create(client).json()["id"]

    res = client.get(f"/api/workstreams/{ws_id}/graph")

    assert res.status_code == 200
    body = res.json()
    assert len(body["nodes"]) == 1
    assert body["edges"] == []
    assert body["primary_task_id"] == body["nodes"][0]["id"]


# --- Focal task node on create (workstream-brain-live-build) ----------------


def _graph(dst, ws_id):
    return json.loads((dst / ws_id / "graph.json").read_text(encoding="utf-8"))


def test_POST_focal_node_id_equals_primary_task_id(tmp_path):
    """primary_task_id points at the seeded focal node in both the 201 body and
    workstream.json, and matches the sole graph node's id."""
    client, dst = _make_client(tmp_path)
    body = _create(client).json()
    ws_id = body["id"]

    graph = _graph(dst, ws_id)
    meta = json.loads((dst / ws_id / "workstream.json").read_text(encoding="utf-8"))
    assert body["primary_task_id"] is not None
    assert body["primary_task_id"] == meta["primary_task_id"]
    assert body["primary_task_id"] == graph["nodes"][0]["id"]


def test_POST_focal_node_title_reflects_name_and_deliverable_type(tmp_path):
    client, dst = _make_client(tmp_path)
    ws_id = _create(
        client, name="Open Finance ED response", deliverable_type="ED"
    ).json()["id"]
    node = _graph(dst, ws_id)["nodes"][0]
    assert node["title"] == "Open Finance ED response (ED)"
    assert node["id"] == "open-finance-ed-response-ed"


def test_POST_focal_node_carries_no_document(tmp_path):
    client, dst = _make_client(tmp_path)
    body = _create(client, name="Climate Risk DP", deliverable_type="DP").json()
    ws_id = body["id"]
    node = _graph(dst, ws_id)["nodes"][0]
    assert "document_id" not in node

    detail = client.get(f"/api/workstreams/{ws_id}/nodes/{node['id']}")
    assert detail.status_code == 200


@pytest.mark.parametrize(
    "name, type_code",
    [
        ("Operational Resilience PD v0.3", "PD"),
        ("Open Finance ED response", "ED"),
        ("Climate Risk DP", "DP"),
        ("RMiT FAQ", "FAQ"),
        ("OpRes Industry Briefing", "DECK"),
        ("OpRes Feedback Form", "FEEDBACK"),
        ("MAS Technology Risk Scan", "BENCHMARK"),
        ("Supervisory Notes compilation", "OTHERS"),
    ],
)
def test_POST_seeds_exactly_one_focal_node_per_deliverable_type(
    tmp_path, name, type_code
):
    client, dst = _make_client(tmp_path)
    ws_id = _create(client, name=name, deliverable_type=type_code).json()["id"]
    nodes = _graph(dst, ws_id)["nodes"]
    assert len(nodes) == 1
    assert nodes[0]["node_type"] == "task"
    assert nodes[0]["title"].endswith(f"({type_code})")
    assert "document_id" not in nodes[0]


def test_POST_new_workstream_appears_in_the_sidebar_list_with_a_role(tmp_path):
    """The sidebar renders `role` as a badge on every row, so a created
    workstream without one would render an empty badge."""
    client, _ = _make_client(tmp_path)
    _create(client)

    listed = client.get("/api/workstreams").json()["workstreams"]

    new = next(w for w in listed if w["id"] == "climate-risk-pd-v2-2026")
    assert new["role"] == "own"
    assert new["deliverable_type"] == "Policy Document"


def test_POST_stores_the_human_deliverable_label_not_the_code(tmp_path):
    """Fixtures store "Policy Document"; the wire takes "PD"."""
    client, _ = _make_client(tmp_path)
    body = _create(client, deliverable_type="ED").json()
    assert body["deliverable_type"] == "Exposure Draft"


@pytest.mark.parametrize(
    "type_code, label",
    [
        ("FAQ", "FAQ"),
        ("DECK", "Engagement Deck"),
        ("FEEDBACK", "Feedback Template for Industry"),
        ("BENCHMARK", "Peer Benchmarking"),
        ("OTHERS", "Others"),
    ],
)
def test_POST_stores_the_label_for_the_newly_expressible_kinds(
    tmp_path, type_code, label
):
    """The four kinds a drafter previously had to record as "Other" — plus
    "Others" itself — each store their own label, so the sidebar stops calling
    an FAQ and an engagement deck the same thing."""
    client, dst = _make_client(tmp_path)
    res = _create(client, name=f"Kind {type_code}", deliverable_type=type_code)
    assert res.status_code == 201
    ws_id = res.json()["id"]
    assert res.json()["deliverable_type"] == label
    meta = json.loads((dst / ws_id / "workstream.json").read_text(encoding="utf-8"))
    assert meta["deliverable_type"] == label


def test_POST_with_only_the_required_fields(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.post(
        "/api/workstreams",
        json={
            "name": "Cyber Risk DP · 2027",
            "deliverable_type": "PD",
            "access": "team_only",
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body["reviewers"] == []
    assert body["description"] is None
    assert body["target_publication"] is None


def test_POST_trims_the_name_and_slugs_from_the_trimmed_value(tmp_path):
    client, _ = _make_client(tmp_path)
    body = _create(client, name="   Spaced Out PD   ").json()
    assert body["name"] == "Spaced Out PD"
    assert body["id"] == "spaced-out-pd"


def test_POST_suffixes_a_colliding_slug_rather_than_overwriting(tmp_path):
    """Two workstreams may legitimately share a name; neither may clobber the
    other's directory."""
    client, dst = _make_client(tmp_path)
    first = _create(client, name="Same Name").json()["id"]
    second = _create(client, name="Same Name").json()["id"]

    assert first == "same-name"
    assert second == "same-name-2"
    assert (dst / first / "workstream.json").exists()
    assert (dst / second / "workstream.json").exists()


def test_POST_does_not_collide_with_a_seeded_workstream(tmp_path):
    client, _ = _make_client(tmp_path)
    body = _create(client, name="opres v2").json()
    assert body["id"] == "opres-v2-2"


def test_POST_name_that_slugifies_to_nothing_still_gets_an_id(tmp_path):
    """A name of pure punctuation (or a non-Latin script) slugifies to ""."""
    client, _ = _make_client(tmp_path)
    body = _create(client, name="!!!").json()
    assert body["id"] == "workstream"


@pytest.mark.parametrize(
    "overrides, code, field",
    [
        ({"name": ""}, "NAME_REQUIRED", "name"),
        ({"name": "   "}, "NAME_REQUIRED", "name"),
        ({"name": _OMIT}, "NAME_REQUIRED", "name"),
        ({"name": "ab"}, "NAME_TOO_SHORT", "name"),
        ({"name": "x" * 121}, "NAME_TOO_LONG", "name"),
        ({"description": "x" * 501}, "DESCRIPTION_TOO_LONG", "description"),
        (
            {"target_publication": "x" * 61},
            "TARGET_PUBLICATION_TOO_LONG",
            "target_publication",
        ),
        (
            {"deliverable_type": "Manifesto"},
            "INVALID_DELIVERABLE_TYPE",
            "deliverable_type",
        ),
        # "Other" was the fourth option of the retired four-code list; the
        # shared vocabulary spells it "OTHERS", and the old spelling is now as
        # invalid as anything else outside the eight.
        (
            {"deliverable_type": "Other"},
            "INVALID_DELIVERABLE_TYPE",
            "deliverable_type",
        ),
        ({"deliverable_type": _OMIT}, "INVALID_DELIVERABLE_TYPE", "deliverable_type"),
        ({"access": "everyone"}, "INVALID_ACCESS", "access"),
        ({"access": _OMIT}, "INVALID_ACCESS", "access"),
    ],
)
def test_POST_rejects_invalid_bodies(tmp_path, overrides, code, field):
    client, _ = _make_client(tmp_path)
    res = _create(client, **overrides)
    assert res.status_code == 400
    body = res.json()
    assert body["code"] == code
    # `field` lets the form flag the offending input rather than a banner.
    assert body["field"] == field


def test_POST_rejects_an_unknown_reviewer(tmp_path):
    client, _ = _make_client(tmp_path)
    res = _create(client, reviewer_ids=["fm", "nobody"])
    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_REVIEWER_ID"


def test_POST_rejects_the_owner_as_their_own_reviewer(tmp_path):
    """Reported, not silently dropped: it is a mistake worth surfacing."""
    client, _ = _make_client(tmp_path)
    res = _create(client, reviewer_ids=["ar"])
    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_REVIEWER_ID"


def test_POST_dedupes_repeated_reviewer_ids(tmp_path):
    client, _ = _make_client(tmp_path)
    body = _create(client, reviewer_ids=["fm", "fm", "ps"]).json()
    assert [r["id"] for r in body["reviewers"]] == ["fm", "ps"]


def test_POST_a_rejected_body_writes_nothing(tmp_path):
    client, dst = _make_client(tmp_path)
    before = {p.name for p in dst.iterdir()}
    _create(client, name="")
    assert {p.name for p in dst.iterdir()} == before


def test_POST_does_not_touch_the_committed_fixture_store(tmp_path):
    """The real data/workstreams/ gains nothing from a test run."""
    client, _ = _make_client(tmp_path)
    _create(client)
    real = {
        p.name for p in (REPO_ROOT / "data" / "workstreams").iterdir() if p.is_dir()
    }
    assert "climate-risk-pd-v2-2026" not in real


# --- Fixture integrity -----------------------------------------------------


def test_seeded_fixtures_use_the_access_enum(tmp_path):
    """The seeded `access` was a list of names — exactly owner + reviewers
    restated. Converted to the policy enum the form actually captures; this
    pins that no fixture drifts back to a list."""
    for path in (REPO_ROOT / "data" / "workstreams").glob("*/workstream.json"):
        ws = json.loads(path.read_text(encoding="utf-8"))
        assert ws["access"] in workstreams.ACCESS_LEVELS, path


# --- The freshly scaffolded focal task is openable --------------------------
# `create_workstream` seeds the focal node with five keys; the seeded fixture
# task nodes carry sixteen. The Task Screen read path must fill the identity
# fields from the workstream record rather than hand the client nulls it will
# dereference.


def test_GET_task_on_a_new_workstream_inherits_owner_from_the_workstream(tmp_path):
    client, _ = _make_client(tmp_path)
    created = _create(client).json()
    body = client.get(
        f"/api/workstreams/{created['id']}/tasks/{created['primary_task_id']}"
    ).json()
    assert body["task"]["owner"] == {"id": "ar", "name": "Aisyah R."}
    assert [r["id"] for r in body["task"]["reviewers"]] == ["fm", "ps"]


def test_GET_task_on_a_new_workstream_reports_an_empty_draft(tmp_path):
    """No document is attached yet — the expected starting state, not an error."""
    client, _ = _make_client(tmp_path)
    created = _create(client).json()
    body = client.get(
        f"/api/workstreams/{created['id']}/tasks/{created['primary_task_id']}"
    ).json()
    assert body["draft_empty"] is True
    assert body["task"]["clause_count"] == 0


def test_GET_task_draft_empty_is_false_once_the_draft_has_content(tmp_path):
    """`clause_count` is never written to the graph, so a live workstream's
    draft state has to come from the saved draft itself."""
    client, _ = _make_client(tmp_path)
    created = _create(client).json()
    ws, task = created["id"], created["primary_task_id"]
    put = client.put(
        f"/api/workstreams/{ws}/tasks/{task}/draft",
        json={"content_html": "<p>1.1 The financial institution shall…</p>"},
    )
    assert put.status_code == 200, put.text
    body = client.get(f"/api/workstreams/{ws}/tasks/{task}").json()
    assert body["draft_empty"] is False
