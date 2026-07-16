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
    return TestClient(create_app(workstreams_dir=dst, analyze_delay=0)), dst


def _create(client, **overrides):
    body = {**VALID, **overrides}
    for k, v in list(body.items()):
        if v is _OMIT:
            del body[k]
    return client.post("/api/workstreams", json=body)


class _Omit:
    pass


_OMIT = _Omit()


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


def test_POST_writes_workstream_json_and_an_empty_graph(tmp_path):
    """The graph must exist: every read path treats a missing graph.json as
    WORKSTREAM_NOT_FOUND, and the form sends the user straight there."""
    client, dst = _make_client(tmp_path)
    ws_id = _create(client).json()["id"]

    meta = json.loads((dst / ws_id / "workstream.json").read_text(encoding="utf-8"))
    graph = json.loads((dst / ws_id / "graph.json").read_text(encoding="utf-8"))
    assert meta["name"] == VALID["name"]
    assert graph == {"nodes": [], "edges": []}


def test_POST_new_workstream_is_immediately_loadable_by_the_graph_route(tmp_path):
    """The round trip the form actually performs: create, then land on it."""
    client, _ = _make_client(tmp_path)
    ws_id = _create(client).json()["id"]

    res = client.get(f"/api/workstreams/{ws_id}/graph")

    assert res.status_code == 200
    body = res.json()
    assert body["nodes"] == []
    assert body["edges"] == []
    assert body["primary_task_id"] is None


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
        ({"deliverable_type": "Manifesto"}, "INVALID_DELIVERABLE_TYPE", "deliverable_type"),
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
    real = {p.name for p in (REPO_ROOT / "data" / "workstreams").iterdir() if p.is_dir()}
    assert "climate-risk-pd-v2-2026" not in real


# --- Fixture integrity -----------------------------------------------------


def test_seeded_fixtures_use_the_access_enum(tmp_path):
    """The seeded `access` was a list of names — exactly owner + reviewers
    restated. Converted to the policy enum the form actually captures; this
    pins that no fixture drifts back to a list."""
    for path in (REPO_ROOT / "data" / "workstreams").glob("*/workstream.json"):
        ws = json.loads(path.read_text(encoding="utf-8"))
        assert ws["access"] in workstreams.ACCESS_LEVELS, path
