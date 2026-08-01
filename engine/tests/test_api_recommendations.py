"""The Recommendations routes: generate from accepted findings, read with coverage.

Fixture discipline follows `test_api_pairwise_findings.py` — each test copies the
seeded `data/workstreams/` into `tmp_path`, so reads double as integrity checks on
the real fixtures while writes touch only the throwaway copy.

**No live model call happens here.** `generate_recommendations_fn` is injected in
every test, and several tests assert the stub was NOT called — which is how the
two 409 gates are proven to fire before the model, not after.

`open-finance-pd-2026` is the fixture that matters. Its task node has ONE edge
and that pair has no findings file at all, while 130 findings hang off edges
between its neighbour and other documents. Any evidence rule narrower than
`workstreams.neighbourhood_edges` therefore yields nothing — the defect the
pairwise route was widened to fix, and this suite guards it for recommendations
too (see `test_evidence_comes_from_the_whole_neighbourhood`).
"""

import json
import shutil

from fastapi.testclient import TestClient

from engine import guardrails, node_metadata, recommendations
from engine.api import create_app
from engine.config import REPO_ROOT

_WS = "open-finance-pd-2026"
_TASK = "open-finance-pd-2026-pd"
_ANCHOR = "rmit-2025"  # a real node, but not a task

_HKMA_EDGE = "e-hkma_open_api_framework--ed_open_finance_2025"
_BIS_EDGE = "e-bis_papers_168--ed_open_finance_2025"

# The six dimensions seeded on the demo working draft, in order.
_DIMENSIONS = [
    "Governance",
    "Participation and scope of information sharing",
    "Transition arrangements",
    "Consent management",
    "Customer protection",
    "Management of technology risk",
]


class _StubGenerator:
    """Records what it was asked, returns what it was told to.

    Captures `dimensions`, `evidence`, `guardrails_body` and `pinned_titles` so a
    test can assert on the PROMPT INPUTS rather than only the output — which is
    how prompt-assembly properties (pinned titles present, guardrails present,
    evidence retained) are verified without a model.
    """

    def __init__(self, payload=None, raise_with=None):
        self.payload = payload if payload is not None else {"recommendations": []}
        self.raise_with = raise_with
        self.calls: list[dict] = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        if self.raise_with is not None:
            raise self.raise_with
        if isinstance(self.payload, str):
            return self.payload
        return json.dumps(self.payload)

    @property
    def called(self) -> bool:
        return bool(self.calls)

    @property
    def last_prompt(self) -> str:
        return recommendations.build_prompt(
            self.calls[-1]["dimensions"],
            self.calls[-1]["evidence"],
            self.calls[-1]["guardrails_body"],
            self.calls[-1]["pinned_titles"],
            self.calls[-1].get("draft_title"),
        )

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


def _make_client(tmp_path, stub=None):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    _scrub_demo_state(dst)
    stub = stub or _StubGenerator()
    app = create_app(workstreams_dir=dst, generate_recommendations_fn=stub)
    return TestClient(app), dst, stub


def _accept(workstreams_dir, edge_id, index, workstream=_WS) -> str:
    """Accept the nth finding on an edge and return its id — the drafter's real
    path, through the same module the review route writes with."""
    from engine import findings as findings_mod

    edge_findings = findings_mod.load(workstreams_dir, workstream, edge_id)
    finding_id = edge_findings[index]["id"]
    findings_mod.set_review_state(
        workstreams_dir, workstream, edge_id, finding_id, "accepted"
    )
    return finding_id


def _rec(finding_ids, title="Publish a data consumer list", dimensions=None):
    return {
        "title": title,
        "rationale": "HKMA requires publication; the ED is silent on it.",
        "action": "Add a requirement to publish authorised data consumers.",
        "dimensions": dimensions or ["Governance"],
        "evidence": [{"finding_id": fid} for fid in finding_ids],
        "confidence_note": "Assumes no industry register already does this.",
    }


def _gen(client, workstream=_WS, node=_TASK):
    return client.post(
        f"/api/workstreams/{workstream}/tasks/{node}/recommendations/generate"
    )


def _get(client, workstream=_WS, node=_TASK):
    return client.get(f"/api/workstreams/{workstream}/tasks/{node}/recommendations")


# ---------------------------------------------------------------------------
# Dimensions (spec Tests 1, 2 — module-level, no HTTP)
# ---------------------------------------------------------------------------


def test_dimension_parsing_splits_strips_and_dedupes():
    """Test 1: one comma-separated line becomes several ordered dimensions."""
    parsed = recommendations.parse_dimensions(
        {"policy_requirement": ["consent management, API security", " consent management ", ""]}
    )
    assert parsed == ["consent management", "API security"]


def test_a_legacy_scalar_policy_requirement_is_tolerated():
    """Test 2: a bare string, as side-files written before the field became a list
    carry. Rejecting it would break a legitimate older profile."""
    assert recommendations.parse_dimensions(
        {"policy_requirement": "consent management, liability"}
    ) == ["consent management", "liability"]


def test_an_absent_profile_or_field_yields_no_dimensions():
    assert recommendations.parse_dimensions(None) == []
    assert recommendations.parse_dimensions({}) == []
    assert recommendations.parse_dimensions({"policy_requirement": None}) == []
    assert recommendations.parse_dimensions({"policy_requirement": []}) == []


# ---------------------------------------------------------------------------
# The two gates (spec Tests 3, 3b, 4)
# ---------------------------------------------------------------------------


def test_generate_is_blocked_without_policy_requirements(tmp_path):
    """Test 3: no dimensions, no generation — and no model call.

    The seeded demo profile means this has to be tested against an explicitly
    emptied state rather than an assumed-absent one.

    Both profile paths are cleared, not just the canonical one: `load_metadata`
    falls back to the legacy `concepts/` directory, so deleting only `metadata/`
    would leave a profile the gate legitimately finds — and the test would fail
    for a reason that has nothing to do with the gate.
    """
    client, workstreams_dir, stub = _make_client(tmp_path)
    for path in (
        node_metadata.metadata_path(workstreams_dir, _WS, _TASK),
        node_metadata.legacy_metadata_path(workstreams_dir, _WS, _TASK),
    ):
        path.unlink(missing_ok=True)
    _accept(workstreams_dir, _HKMA_EDGE, 0)

    response = _gen(client)

    assert response.status_code == 409
    assert response.json()["code"] == "NO_POLICY_REQUIREMENTS"
    assert not stub.called, "the gate must fire before the model is called"
    assert not recommendations.recommendations_path(
        workstreams_dir, _WS, _TASK
    ).exists()


def test_the_seeded_demo_profile_satisfies_the_gate(tmp_path):
    """Test 3b: the demo path itself, asserted directly.

    The six dimensions are the demo's entry condition. If this list drifts,
    generation reasons over the wrong axes.
    """
    stub = _StubGenerator({"recommendations": []})
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    _accept(workstreams_dir, _HKMA_EDGE, 0)

    response = _gen(client)

    assert response.status_code == 201
    assert response.json()["dimensions"] == _DIMENSIONS
    assert stub.calls[0]["dimensions"] == _DIMENSIONS


def test_generate_is_blocked_without_accepted_findings(tmp_path):
    """Test 4: pending findings are not evidence, and the model is not called."""
    client, _workstreams_dir, stub = _make_client(tmp_path)

    response = _gen(client)

    assert response.status_code == 409
    assert response.json()["code"] == "NO_ACCEPTED_FINDINGS"
    assert not stub.called


def test_dismissed_findings_are_not_evidence(tmp_path):
    """A dismissed finding is a judgement against it — it must not resurface as
    support for a recommendation."""
    from engine import findings as findings_mod

    client, workstreams_dir, stub = _make_client(tmp_path)
    edge_findings = findings_mod.load(workstreams_dir, _WS, _HKMA_EDGE)
    findings_mod.set_review_state(
        workstreams_dir, _WS, _HKMA_EDGE, edge_findings[0]["id"], "dismissed"
    )

    response = _gen(client)

    assert response.status_code == 409
    assert response.json()["code"] == "NO_ACCEPTED_FINDINGS"


# ---------------------------------------------------------------------------
# Evidence scope (spec Test 5)
# ---------------------------------------------------------------------------


def test_evidence_comes_from_the_whole_neighbourhood(tmp_path):
    """Test 5: a second-order acceptance is evidence.

    The task's own edge has no findings file at all, so every acceptance a
    drafter can make on this fixture is second-order. A narrower rule yields
    nothing — this is the exact defect the pairwise route was widened to fix.
    """
    client, workstreams_dir, stub = _make_client(tmp_path)
    accepted_id = _accept(workstreams_dir, _HKMA_EDGE, 0)

    response = _gen(client)

    assert response.status_code == 201
    assert response.json()["accepted_count"] == 1
    handed = [item["finding_id"] for item in stub.calls[0]["evidence"]]
    assert handed == [accepted_id]


def test_the_generate_scope_matches_the_pairwise_box(tmp_path):
    """The two surfaces must agree about what is in scope, because they call the
    same `neighbourhood_edges`. Asserted by comparing counts rather than trusting
    the shared call."""
    client, workstreams_dir, _stub = _make_client(tmp_path)
    for index in range(3):
        _accept(workstreams_dir, _HKMA_EDGE, index)

    box = client.get(
        f"/api/workstreams/{_WS}/tasks/{_TASK}/pairwise-findings"
    ).json()
    accepted_in_box = sum(
        1 for f in box["findings"] if f["review_state"] == "accepted"
    )

    assert _get(client).json()["accepted_count"] == accepted_in_box == 3


# ---------------------------------------------------------------------------
# The evidence floor (spec Tests 6, 7)
# ---------------------------------------------------------------------------


def test_an_unsupported_recommendation_is_dropped(tmp_path):
    """Test 6: a hallucinated finding_id gets its recommendation dropped, not
    published. This is the citation rule being ENFORCED, not requested."""
    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    real = _accept(workstreams_dir, _HKMA_EDGE, 0)
    stub.payload = {
        "recommendations": [
            _rec([real], title="Supported"),
            _rec(["does-not-exist"], title="Unsupported"),
        ]
    }

    body = _gen(client).json()

    assert body["dropped_unsupported"] == 1
    assert [rec["title"] for rec in body["recommendations"]] == ["Supported"]
    stored = json.loads(
        recommendations.recommendations_path(workstreams_dir, _WS, _TASK).read_text(
            encoding="utf-8"
        )
    )
    assert [rec["title"] for rec in stored["recommendations"]] == ["Supported"]


def test_a_recommendation_citing_nothing_at_all_is_dropped(tmp_path):
    stub = _StubGenerator({"recommendations": [_rec([], title="Bare assertion")]})
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    _accept(workstreams_dir, _HKMA_EDGE, 0)

    body = _gen(client).json()

    assert body["recommendations"] == []
    assert body["dropped_unsupported"] == 1


def test_clause_text_is_copied_verbatim_from_the_finding(tmp_path):
    """Test 7: the persisted evidence carries OUR clause text, read off the
    finding — not the model's paraphrase of it. A recommendation cannot cite text
    its own evidence does not contain."""
    from engine import findings as findings_mod

    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    accepted = _accept(workstreams_dir, _HKMA_EDGE, 0)
    source_finding = next(
        f
        for f in findings_mod.load(workstreams_dir, _WS, _HKMA_EDGE)
        if f["id"] == accepted
    )
    expected_text = source_finding["source_clauses"][0]["text"]

    stub.payload = {
        "recommendations": [
            {
                **_rec([accepted]),
                # The model tries to supply its own clause text; it must be
                # ignored in favour of the finding's own.
                "evidence": [
                    {
                        "finding_id": accepted,
                        "source_clause_text": "PARAPHRASED BY THE MODEL",
                    }
                ],
            }
        ]
    }

    evidence = _gen(client).json()["recommendations"][0]["evidence"][0]

    assert evidence["source_clause_text"] == expected_text
    assert "PARAPHRASED BY THE MODEL" not in json.dumps(evidence)


# ---------------------------------------------------------------------------
# Bookmarks + prompt assembly (spec Tests 8, 9)
# ---------------------------------------------------------------------------


def _bookmark_first(workstreams_dir, workstream=_WS, node=_TASK) -> dict:
    """Mark the first recommendation bookmarked directly on disk — the PATCH route
    belongs to a later story, and this story's guarantee is about survival."""
    path = recommendations.recommendations_path(workstreams_dir, workstream, node)
    record = json.loads(path.read_text(encoding="utf-8"))
    record["recommendations"][0]["bookmarked"] = True
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return record["recommendations"][0]


def test_a_bookmarked_recommendation_survives_regeneration_byte_for_byte(tmp_path):
    """Test 8: regenerating must not cost the drafter a decision she made."""
    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    accepted = _accept(workstreams_dir, _HKMA_EDGE, 0)

    stub.payload = {"recommendations": [_rec([accepted], title="Keep me")]}
    _gen(client)
    pinned = _bookmark_first(workstreams_dir)

    stub.payload = {
        "recommendations": [
            _rec([accepted], title="Brand new one"),
            _rec([accepted], title="Another new one"),
        ]
    }
    body = _gen(client).json()

    titles = [rec["title"] for rec in body["recommendations"]]
    assert titles == ["Keep me", "Brand new one", "Another new one"]
    survivor = body["recommendations"][0]
    assert survivor == pinned, "a bookmarked recommendation must survive unchanged"
    assert survivor["id"] == pinned["id"]


def test_pinned_titles_reach_the_prompt_as_do_not_restate(tmp_path):
    """Test 9: the only reason a bookmark enters the next generation at all."""
    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    accepted = _accept(workstreams_dir, _HKMA_EDGE, 0)

    stub.payload = {"recommendations": [_rec([accepted], title="Publish the list")]}
    _gen(client)
    _bookmark_first(workstreams_dir)

    _gen(client)

    assert stub.calls[-1]["pinned_titles"] == ["Publish the list"]
    prompt = stub.last_prompt
    assert "Publish the list" in prompt
    assert "Do NOT" in prompt and "restate" in prompt


def test_a_pinned_recommendations_evidence_stays_available(tmp_path):
    """A finding that bears on two dimensions must still be able to support a new
    recommendation about the second. Withholding it would silently drop it."""
    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    accepted = _accept(workstreams_dir, _HKMA_EDGE, 0)

    stub.payload = {"recommendations": [_rec([accepted], title="First use")]}
    _gen(client)
    _bookmark_first(workstreams_dir)

    _gen(client)

    handed = [item["finding_id"] for item in stub.calls[-1]["evidence"]]
    assert accepted in handed


def test_the_guardrails_reach_the_generation_prompt(tmp_path):
    """Test 17 (prompt half): an edit takes effect on the very next generation."""
    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    _accept(workstreams_dir, _HKMA_EDGE, 0)
    guardrails.save(
        workstreams_dir, _WS, "Never cite another policy document by provision number."
    )

    _gen(client)

    prompt = stub.last_prompt
    assert "Never cite another policy document by provision number." in prompt
    assert "1. House convention" not in prompt, "the saved body replaces the defaults"


def test_the_default_guardrails_reach_the_prompt_when_none_are_saved(tmp_path):
    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    _accept(workstreams_dir, _HKMA_EDGE, 0)

    _gen(client)

    assert "provision number" in stub.last_prompt


def test_emptied_guardrails_add_no_block_to_the_prompt(tmp_path):
    """Clearing the box means it — the defaults must not creep back in via the
    prompt after the drafter deleted them."""
    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    _accept(workstreams_dir, _HKMA_EDGE, 0)
    guardrails.save(workstreams_dir, _WS, "")

    _gen(client)

    assert "GUARDRAILS" not in stub.last_prompt


# ---------------------------------------------------------------------------
# Failure isolation (spec Tests 10, 11)
# ---------------------------------------------------------------------------


def test_a_failed_generation_leaves_the_previous_set_intact(tmp_path):
    """Test 10: the drafter does not lose a good set to a bad model call."""
    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    accepted = _accept(workstreams_dir, _HKMA_EDGE, 0)

    stub.payload = {"recommendations": [_rec([accepted], title="Yesterday's set")]}
    _gen(client)
    path = recommendations.recommendations_path(workstreams_dir, _WS, _TASK)
    before = path.read_bytes()

    stub.raise_with = RuntimeError("model unavailable")
    response = _gen(client)

    assert response.status_code == 502
    assert response.json()["code"] == "RECOMMENDATIONS_FAILED"
    assert path.read_bytes() == before
    assert [rec["title"] for rec in _get(client).json()["recommendations"]] == [
        "Yesterday's set"
    ]


def test_a_malformed_model_response_is_a_502_not_a_crash(tmp_path):
    """Test 11: unparseable output is an upstream failure, reported as one."""
    stub = _StubGenerator("not json at all")
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    _accept(workstreams_dir, _HKMA_EDGE, 0)

    response = _gen(client)

    assert response.status_code == 502
    assert response.json()["code"] == "RECOMMENDATIONS_FAILED"
    assert not recommendations.recommendations_path(
        workstreams_dir, _WS, _TASK
    ).exists()


def test_a_response_without_a_recommendations_array_is_a_502(tmp_path):
    stub = _StubGenerator({"something_else": []})
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    _accept(workstreams_dir, _HKMA_EDGE, 0)

    assert _gen(client).status_code == 502


def test_a_bare_json_array_is_accepted(tmp_path):
    """A model that returns the array directly instead of wrapping it is fine —
    failing an otherwise-good generation on that technicality would be brittle."""
    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    accepted = _accept(workstreams_dir, _HKMA_EDGE, 0)
    stub.payload = [_rec([accepted], title="Bare array")]

    body = _gen(client).json()

    assert [rec["title"] for rec in body["recommendations"]] == ["Bare array"]


# ---------------------------------------------------------------------------
# Reading + coverage (spec Tests 12, 13)
# ---------------------------------------------------------------------------


def test_reading_before_any_generation_is_not_an_error(tmp_path):
    """Test 12: the card's empty states are data, not error handling."""
    client, workstreams_dir, _ = _make_client(tmp_path)
    accepted = _accept(workstreams_dir, _HKMA_EDGE, 0)

    body = _get(client).json()

    assert body["generated_at"] is None
    assert body["recommendations"] == []
    assert body["dimensions"] == _DIMENSIONS
    assert body["accepted_count"] == 1
    assert [item["finding_id"] for item in body["not_yet_reflected"]] == [accepted]


def test_coverage_is_derived_and_tracks_review_state(tmp_path):
    """Test 13: a persisted figure would drift the moment a review state changed."""
    from engine import findings as findings_mod

    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    cited = _accept(workstreams_dir, _HKMA_EDGE, 0)
    uncited_a = _accept(workstreams_dir, _HKMA_EDGE, 1)
    _accept(workstreams_dir, _HKMA_EDGE, 2)

    stub.payload = {"recommendations": [_rec([cited])]}
    _gen(client)
    path = recommendations.recommendations_path(workstreams_dir, _WS, _TASK)
    after_generate = path.read_bytes()

    first = _get(client).json()
    assert first["counts"]["not_yet_reflected"] == 2
    assert first["counts"]["cited_findings"] == 1

    findings_mod.set_review_state(
        workstreams_dir, _WS, _HKMA_EDGE, uncited_a, "dismissed"
    )
    second = _get(client).json()

    assert second["counts"]["not_yet_reflected"] == 1
    assert path.read_bytes() == after_generate, "a read must not rewrite the file"


def test_coverage_is_empty_when_everything_is_cited(tmp_path):
    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    accepted = _accept(workstreams_dir, _HKMA_EDGE, 0)

    stub.payload = {"recommendations": [_rec([accepted])]}
    _gen(client)

    body = _get(client).json()
    assert body["not_yet_reflected"] == []
    assert body["counts"]["not_yet_reflected"] == 0


def test_coverage_spans_edges_and_does_not_double_count(tmp_path):
    """One finding cited by two recommendations is still one cited finding."""
    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    hkma = _accept(workstreams_dir, _HKMA_EDGE, 0)
    _accept(workstreams_dir, _BIS_EDGE, 0)

    stub.payload = {
        "recommendations": [_rec([hkma], title="One"), _rec([hkma], title="Two")]
    }
    _gen(client)

    counts = _get(client).json()["counts"]
    assert counts["cited_findings"] == 1
    assert counts["not_yet_reflected"] == 1


def test_recommendations_survive_leaving_and_returning(tmp_path):
    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    accepted = _accept(workstreams_dir, _HKMA_EDGE, 0)
    stub.payload = {"recommendations": [_rec([accepted], title="This morning")]}
    _gen(client)

    body = _get(client).json()

    assert [rec["title"] for rec in body["recommendations"]] == ["This morning"]
    assert body["generated_at"] is not None


# ---------------------------------------------------------------------------
# Node resolution + ids (spec Tests 14, 15, 22, 23)
# ---------------------------------------------------------------------------


def test_a_non_task_node_is_refused(tmp_path):
    """Test 14: a published document has nothing to change, so no recommendations."""
    client, _workstreams_dir, _ = _make_client(tmp_path)

    for response in (_get(client, node=_ANCHOR), _gen(client, node=_ANCHOR)):
        assert response.status_code == 400
        assert response.json()["code"] == "NOT_A_TASK"


def test_a_missing_node_is_distinguished_from_a_non_task_node(tmp_path):
    """Test 15: the same three-way distinction the pairwise box draws."""
    client, _workstreams_dir, _ = _make_client(tmp_path)

    missing = _get(client, node="no-such-node")
    assert missing.status_code == 404
    assert missing.json()["code"] == "NODE_NOT_FOUND"

    unknown_ws = _get(client, workstream="no-such-ws")
    assert unknown_ws.status_code == 404
    assert unknown_ws.json()["code"] == "WORKSTREAM_NOT_FOUND"


def test_a_traversal_in_the_node_id_is_refused(tmp_path):
    """Test 22: `node_id` interpolates into a filesystem path, so it is resolved
    against the loaded graph before anything is read or written."""
    client, workstreams_dir, _ = _make_client(tmp_path)

    response = client.get(
        f"/api/workstreams/{_WS}/tasks/..%2F..%2Fetc/recommendations"
    )

    # Starlette's router refuses the encoded traversal before the handler is
    # reached, so this is a framework 404 (`detail`) rather than our
    # `NODE_NOT_FOUND` envelope. Either way nothing is read or written outside
    # the workstream, which is the property that matters.
    assert response.status_code == 404
    assert not (workstreams_dir.parent / "recommendations").exists()

    # A node id that IS routable but absent from the graph reaches our guard and
    # gets the honest code — the resolution step is doing real work.
    unrouted = client.get(
        f"/api/workstreams/{_WS}/tasks/..-..-etc/recommendations"
    )
    assert unrouted.status_code == 404
    assert unrouted.json()["code"] == "NODE_NOT_FOUND"


def test_recommendation_ids_are_opaque_not_index_derived(tmp_path):
    """Test 23: an index-derived id would silently re-point a bookmark at a
    different recommendation after a regeneration reorders the list."""
    import re

    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    accepted = _accept(workstreams_dir, _HKMA_EDGE, 0)

    stub.payload = {
        "recommendations": [_rec([accepted], title="A"), _rec([accepted], title="B")]
    }
    first_ids = [rec["id"] for rec in _gen(client).json()["recommendations"]]

    stub.payload = {"recommendations": [_rec([accepted], title="C")]}
    second_ids = [rec["id"] for rec in _gen(client).json()["recommendations"]]

    for rec_id in first_ids + second_ids:
        assert re.fullmatch(r"[0-9a-f]{12}", rec_id), rec_id
        assert "~" not in rec_id
    assert not set(first_ids) & set(second_ids), "ids must not be reused"


def test_a_generated_recommendation_carries_every_field(tmp_path):
    """The persisted shape is what the interface reads; a missing key would render
    as `undefined` rather than an honest empty state."""
    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    accepted = _accept(workstreams_dir, _HKMA_EDGE, 0)
    stub.payload = {"recommendations": [_rec([accepted])]}

    rec = _gen(client).json()["recommendations"][0]

    for field in recommendations.RECOMMENDATION_FIELDS:
        assert field in rec, field
    assert rec["bookmarked"] is False
    assert rec["comments"] == []
    assert rec["revisions"] == []
    assert rec["dimensions"] == ["Governance"]
    assert rec["confidence_note"]


def test_retired_fixtures_get_no_recommendations_directory(tmp_path):
    """Reading a retired fixture must not create a file inside it."""
    client, workstreams_dir, _ = _make_client(tmp_path)

    client.get(
        "/api/workstreams/opres-v2/tasks/opres-pd-v0-3/recommendations"
    )

    assert not (workstreams_dir / "opres-v2" / "recommendations").exists()


# ---------------------------------------------------------------------------
# The committed demo seed
#
# Unlike every test above, these read the TRACKED fixture rather than a scrubbed
# copy — the point is precisely that the demo ships ready to run. Read-only.
# ---------------------------------------------------------------------------


def _demo_seed() -> dict:
    path = recommendations.recommendations_path(
        REPO_ROOT / "data" / "workstreams", _WS, _TASK
    )
    assert path.exists(), (
        "the demo's pre-generated recommendations are missing — the demo needs "
        "them to run without a model call"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_the_committed_demo_seed_is_generated_and_non_empty():
    """The demo runs from committed output, so no model call is needed on the day
    (the build-and-persist strategy in CLAUDE.md)."""
    seed = _demo_seed()

    assert seed["generated_at"] is not None
    assert seed["dimensions_used"] == _DIMENSIONS
    assert len(seed["recommendations"]) >= 1


def test_every_committed_recommendation_cites_a_real_accepted_finding():
    """The evidence floor, asserted against the SHIPPED data rather than a stub.

    This is the one test that would catch a hand-authored or stale seed: a
    recommendation citing a finding that is not accepted in the tracked fixture
    would pass every other test in this file and fail here.
    """
    from engine import workstreams as ws_mod

    workstreams_dir = REPO_ROOT / "data" / "workstreams"
    ws_graph = ws_mod.load_graph(workstreams_dir, _WS)
    accepted = {
        item["finding_id"]: item
        for item in recommendations.collect_evidence(
            workstreams_dir, _WS, _TASK, ws_graph
        )
    }
    assert accepted, "the demo needs accepted findings for its seed to rest on"

    for rec in _demo_seed()["recommendations"]:
        assert rec["evidence"], f"{rec['id']} cites nothing"
        for citation in rec["evidence"]:
            assert citation["finding_id"] in accepted, (
                f"{rec['id']} cites {citation['finding_id']}, which is not an "
                "accepted finding in the tracked fixture"
            )
            # Clause text must be the finding's own, character for character —
            # the verbatim-citation guarantee, checked on shipped data.
            source = accepted[citation["finding_id"]]
            for field in (
                "source_clause_number",
                "source_clause_text",
                "target_clause_number",
                "target_clause_text",
            ):
                assert citation[field] == source[field], (
                    f"{rec['id']} altered {field} on {citation['finding_id']}"
                )


def test_every_committed_recommendation_carries_the_full_shape():
    """A missing key would render as `undefined` in the card rather than an
    honest empty state."""
    for rec in _demo_seed()["recommendations"]:
        for field in recommendations.RECOMMENDATION_FIELDS:
            assert field in rec, f"{rec['id']} is missing {field}"
        assert rec["confidence_note"].strip(), (
            f"{rec['id']} has no confidence note — every recommendation must "
            "state what it could not verify"
        )
        assert rec["dimensions"], f"{rec['id']} is tagged with no dimension"
        for dimension in rec["dimensions"]:
            assert dimension in _DIMENSIONS, (
                f"{rec['id']} invented the dimension {dimension!r}"
            )


def test_the_demo_seed_serves_through_the_route_with_coverage():
    """End to end on the tracked fixture: the card's own read path."""
    client = TestClient(create_app())

    body = _get(client).json()

    assert body["generated_at"] is not None
    assert body["dimensions"] == _DIMENSIONS
    assert body["counts"]["total"] == len(_demo_seed()["recommendations"])
    # Coverage is derived, so these must add up against the accepted set.
    assert (
        body["counts"]["cited_findings"] + body["counts"]["not_yet_reflected"]
        == body["accepted_count"]
    )


# ---------------------------------------------------------------------------
# Rationale normalisation
#
# The prompt asks for a `- ` bullet list. A model honours that as a string with
# newlines OR as a JSON array of bullets — both were observed against the live
# model. `str()` on the array would render `['- one', '- two']` on the card,
# brackets and quotes included, so the shape is normalised in the engine rather
# than left for the frontend to guess at.
# ---------------------------------------------------------------------------


def test_a_rationale_returned_as_a_json_array_is_normalised(tmp_path):
    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    accepted = _accept(workstreams_dir, _HKMA_EDGE, 0)
    stub.payload = {
        "recommendations": [
            {
                **_rec([accepted]),
                "rationale": [
                    "- ED S 10.4 requires a real-time consent dashboard.",
                    "- HKMA sets no equivalent requirement.",
                ],
            }
        ]
    }

    rationale = _gen(client).json()["recommendations"][0]["rationale"]

    assert rationale == (
        "- ED S 10.4 requires a real-time consent dashboard.\n"
        "- HKMA sets no equivalent requirement."
    )
    # The failure this guards against is cosmetic but glaring: Python's repr of
    # the list reaching the card verbatim.
    assert "[" not in rationale and "'" not in rationale


def test_bullet_markers_are_normalised_and_added_where_missing(tmp_path):
    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    accepted = _accept(workstreams_dir, _HKMA_EDGE, 0)
    stub.payload = {
        "recommendations": [
            {
                **_rec([accepted]),
                # Mixed markers, and one item with none at all.
                "rationale": ["* First point.", "• Second point.", "Third point."],
            }
        ]
    }

    rationale = _gen(client).json()["recommendations"][0]["rationale"]

    assert rationale.split("\n") == [
        "- First point.",
        "- Second point.",
        "- Third point.",
    ]


def test_a_single_paragraph_rationale_is_left_as_prose(tmp_path):
    """A model that ignores the bullet instruction still reads correctly — forcing
    a bullet onto continuous prose would imply a structure it did not write."""
    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    accepted = _accept(workstreams_dir, _HKMA_EDGE, 0)
    stub.payload = {
        "recommendations": [
            {**_rec([accepted]), "rationale": "One continuous paragraph."}
        ]
    }

    rationale = _gen(client).json()["recommendations"][0]["rationale"]

    assert rationale == "One continuous paragraph."


def test_the_prompt_states_the_hard_field_limits(tmp_path):
    """The style limits are what keep the output readable, and they were arrived
    at by observing the model ignore softer phrasing. Pin the ones that matter."""
    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    _accept(workstreams_dir, _HKMA_EDGE, 0)

    _gen(client)

    system = recommendations._SYSTEM_PROMPT
    assert "MAXIMUM 80 characters" in system  # title
    assert "MAXIMUM 25 words" in system  # confidence_note
    assert "Never return the rationale as continuous prose." in system
    assert "Nothing unverified." in system


# ---------------------------------------------------------------------------
# Bookmarking (Story 2 — the drafter taking a recommendation forward)
# ---------------------------------------------------------------------------


def _patch(client, rec_id, body, workstream=_WS, node=_TASK):
    return client.patch(
        f"/api/workstreams/{workstream}/tasks/{node}/recommendations/{rec_id}",
        json=body,
    )


def _generate_one(tmp_path):
    """A client with exactly one generated recommendation, and its id."""
    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    accepted = _accept(workstreams_dir, _HKMA_EDGE, 0)
    stub.payload = {"recommendations": [_rec([accepted], title="Take me forward")]}
    rec_id = _gen(client).json()["recommendations"][0]["id"]
    return client, workstreams_dir, stub, rec_id


def test_bookmarking_persists(tmp_path):
    client, workstreams_dir, _stub, rec_id = _generate_one(tmp_path)

    response = _patch(client, rec_id, {"bookmarked": True})

    assert response.status_code == 200
    assert response.json()["bookmarked"] is True
    stored = json.loads(
        recommendations.recommendations_path(
            workstreams_dir, _WS, _TASK
        ).read_text(encoding="utf-8")
    )
    assert stored["recommendations"][0]["bookmarked"] is True
    assert _get(client).json()["counts"]["bookmarked"] == 1


def test_unbookmarking_persists(tmp_path):
    client, _workstreams_dir, _stub, rec_id = _generate_one(tmp_path)
    _patch(client, rec_id, {"bookmarked": True})

    response = _patch(client, rec_id, {"bookmarked": False})

    assert response.status_code == 200
    assert response.json()["bookmarked"] is False
    assert _get(client).json()["counts"]["bookmarked"] == 0


def test_bookmarking_is_idempotent(tmp_path):
    """Her intent is the same either way, so there is no "already bookmarked"
    error to raise."""
    client, _workstreams_dir, _stub, rec_id = _generate_one(tmp_path)

    first = _patch(client, rec_id, {"bookmarked": True})
    second = _patch(client, rec_id, {"bookmarked": True})

    assert first.status_code == second.status_code == 200
    assert second.json()["bookmarked"] is True
    assert _get(client).json()["counts"]["bookmarked"] == 1


def test_bookmarking_makes_no_model_call(tmp_path):
    client, _workstreams_dir, stub, rec_id = _generate_one(tmp_path)
    calls_before = len(stub.calls)

    _patch(client, rec_id, {"bookmarked": True})

    assert len(stub.calls) == calls_before


def test_a_bookmark_survives_regeneration_through_the_route(tmp_path):
    """The whole point of the flag: regenerating must not cost the drafter a
    decision she made. Story 1 proves this with a hand-set flag; this proves it
    through the route a drafter actually uses."""
    client, workstreams_dir, stub, rec_id = _generate_one(tmp_path)
    _patch(client, rec_id, {"bookmarked": True})
    pinned = next(
        rec
        for rec in _get(client).json()["recommendations"]
        if rec["id"] == rec_id
    )

    accepted = _accept(workstreams_dir, _HKMA_EDGE, 1)
    stub.payload = {"recommendations": [_rec([accepted], title="Fresh one")]}
    body = _gen(client).json()

    titles = [rec["title"] for rec in body["recommendations"]]
    assert titles == ["Take me forward", "Fresh one"]
    assert body["recommendations"][0] == pinned


def test_an_unknown_recommendation_id_is_a_404(tmp_path):
    client, workstreams_dir, _stub, _rec_id = _generate_one(tmp_path)
    before = recommendations.recommendations_path(
        workstreams_dir, _WS, _TASK
    ).read_bytes()

    response = _patch(client, "deadbeef0000", {"bookmarked": True})

    assert response.status_code == 404
    assert response.json()["code"] == "RECOMMENDATION_NOT_FOUND"
    assert response.json()["message"] == "No recommendation deadbeef0000 on this task."
    assert (
        recommendations.recommendations_path(
            workstreams_dir, _WS, _TASK
        ).read_bytes()
        == before
    )


def test_patching_before_anything_is_generated_is_a_404(tmp_path):
    """Distinguished from an unknown id: nothing has been generated at all, which
    is a different thing to tell the drafter."""
    client, _workstreams_dir, _stub = _make_client(tmp_path)

    response = _patch(client, "4f9f91c02ef5", {"bookmarked": True})

    assert response.status_code == 404
    assert response.json()["code"] == "RECOMMENDATIONS_NOT_GENERATED"


def test_a_non_boolean_bookmarked_is_refused(tmp_path):
    client, workstreams_dir, _stub, rec_id = _generate_one(tmp_path)
    before = recommendations.recommendations_path(
        workstreams_dir, _WS, _TASK
    ).read_bytes()

    # 1 and 0 matter: `isinstance(True, int)` is True in Python, so a numeric
    # coercion would silently accept them and store a non-bool.
    for bad in ("yes", 1, 0, None, ["true"]):
        response = _patch(client, rec_id, {"bookmarked": bad})
        assert response.status_code == 400, bad
        assert response.json()["code"] == "INVALID_PATCH"
        assert response.json()["message"] == "bookmarked must be a boolean."

    assert (
        recommendations.recommendations_path(
            workstreams_dir, _WS, _TASK
        ).read_bytes()
        == before
    )


def test_a_patch_with_no_recognised_field_is_refused(tmp_path):
    client, _workstreams_dir, _stub, rec_id = _generate_one(tmp_path)

    assert _patch(client, rec_id, {}).status_code == 400
    assert _patch(client, rec_id, {"title": "hijacked"}).status_code == 400


def test_patching_a_non_task_node_is_refused(tmp_path):
    client, _workstreams_dir, _stub, rec_id = _generate_one(tmp_path)

    response = _patch(client, rec_id, {"bookmarked": True}, node=_ANCHOR)

    assert response.status_code == 400
    assert response.json()["code"] == "NOT_A_TASK"


# ---------------------------------------------------------------------------
# Comments and rewriting (Story 3)
#
# The defining constraint: a comment stays ON ITS CARD. Nothing here writes to
# the guardrails — promoting a situated note into a standing rule would have a
# model authoring the rules it then follows.
# ---------------------------------------------------------------------------


def test_a_comment_persists_with_author_and_timestamp(tmp_path):
    client, workstreams_dir, _stub, rec_id = _generate_one(tmp_path)

    response = _patch(
        client, rec_id, {"comment": "HKMA's TSP is not our TPSP."}
    )

    assert response.status_code == 200
    comments = response.json()["comments"]
    assert len(comments) == 1
    assert comments[0]["text"] == "HKMA's TSP is not our TPSP."
    assert comments[0]["author"]["name"]
    assert comments[0]["at"].endswith("Z")
    # The recommendation itself is untouched — commenting is not rewriting.
    assert response.json()["title"] == "Take me forward"


def test_commenting_makes_no_model_call(tmp_path):
    """Test 2: recording a caveat must not spend a model call."""
    client, _workstreams_dir, stub, rec_id = _generate_one(tmp_path)
    before = len(stub.calls)

    _patch(client, rec_id, {"comment": "A note for later."})

    assert len(stub.calls) == before


def test_several_comments_accumulate_oldest_first(tmp_path):
    client, _workstreams_dir, _stub, rec_id = _generate_one(tmp_path)

    _patch(client, rec_id, {"comment": "First point."})
    response = _patch(client, rec_id, {"comment": "Second point."})

    texts = [c["text"] for c in response.json()["comments"]]
    assert texts == ["First point.", "Second point."]


def test_a_whitespace_only_comment_is_refused(tmp_path):
    """Test 3."""
    client, workstreams_dir, _stub, rec_id = _generate_one(tmp_path)
    before = recommendations.recommendations_path(
        workstreams_dir, _WS, _TASK
    ).read_bytes()

    response = _patch(client, rec_id, {"comment": "   \n  "})

    assert response.status_code == 400
    assert response.json()["code"] == "EMPTY_COMMENT"
    assert response.json()["message"] == "A comment cannot be empty."
    assert (
        recommendations.recommendations_path(
            workstreams_dir, _WS, _TASK
        ).read_bytes()
        == before
    )


def test_an_oversized_comment_is_refused(tmp_path):
    """Test 4."""
    client, _workstreams_dir, _stub, rec_id = _generate_one(tmp_path)

    response = _patch(
        client,
        rec_id,
        {"comment": "x" * (recommendations.MAX_COMMENT_CHARS + 1)},
    )

    assert response.status_code == 413
    assert response.json()["code"] == "COMMENT_TOO_LARGE"


def test_a_non_string_comment_is_refused(tmp_path):
    """Test 5."""
    client, _workstreams_dir, _stub, rec_id = _generate_one(tmp_path)

    response = _patch(client, rec_id, {"comment": 42})

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_PATCH"
    assert response.json()["message"] == "comment must be a string."


def test_a_comment_and_a_bookmark_in_one_request(tmp_path):
    """Test 6."""
    client, _workstreams_dir, _stub, rec_id = _generate_one(tmp_path)

    response = _patch(
        client, rec_id, {"comment": "Scope is banking only.", "bookmarked": True}
    )

    assert response.status_code == 200
    assert response.json()["bookmarked"] is True
    assert len(response.json()["comments"]) == 1


def test_nothing_writes_to_the_guardrails(tmp_path):
    """Test 16 — the one that would catch a regression reintroducing automatic
    promotion. Keep it."""
    client, workstreams_dir, _stub, rec_id = _generate_one(tmp_path)
    assert not guardrails.guardrails_path(workstreams_dir, _WS).exists()

    _patch(client, rec_id, {"comment": "BNM never cites by provision number."})
    _rewrite(client, rec_id)

    assert not guardrails.guardrails_path(workstreams_dir, _WS).exists()
    served = client.get(f"/api/workstreams/{_WS}/guardrails").json()
    assert served["is_default"] is True


def _rewrite(client, rec_id, workstream=_WS, node=_TASK):
    return client.post(
        f"/api/workstreams/{workstream}/tasks/{node}"
        f"/recommendations/{rec_id}/rewrite"
    )


def test_a_rewrite_preserves_identity(tmp_path):
    """Test 7: id, bookmark, dimensions, comments and list position all carry."""
    client, workstreams_dir, stub, rec_id = _generate_one(tmp_path)
    _patch(client, rec_id, {"bookmarked": True, "comment": "Reframe this."})
    accepted = _get(client).json()["recommendations"][0]["evidence"][0][
        "finding_id"
    ]

    stub.payload = {
        "recommendations": [_rec([accepted], title="Rewritten wording")]
    }
    response = _rewrite(client, rec_id)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == rec_id
    assert body["bookmarked"] is True
    assert body["dimensions"] == ["Governance"]
    assert len(body["comments"]) == 1
    assert body["title"] == "Rewritten wording"


def test_a_rewrite_appends_the_previous_version(tmp_path):
    """Test 8: the change is visible, not silent. `evidence` is deliberately not
    snapshotted — it projects findings that still exist."""
    client, workstreams_dir, stub, rec_id = _generate_one(tmp_path)
    original = _get(client).json()["recommendations"][0]
    accepted = original["evidence"][0]["finding_id"]

    stub.payload = {"recommendations": [_rec([accepted], title="Version two")]}
    body = _rewrite(client, rec_id).json()

    assert len(body["revisions"]) == 1
    revision = body["revisions"][0]
    assert revision["title"] == original["title"]
    assert revision["action"] == original["action"]
    assert revision["at"].endswith("Z")
    assert "evidence" not in revision


def test_two_rewrites_append_two_revisions_in_order(tmp_path):
    """Test 9."""
    client, _workstreams_dir, stub, rec_id = _generate_one(tmp_path)
    accepted = _get(client).json()["recommendations"][0]["evidence"][0][
        "finding_id"
    ]

    stub.payload = {"recommendations": [_rec([accepted], title="Second")]}
    _rewrite(client, rec_id)
    stub.payload = {"recommendations": [_rec([accepted], title="Third")]}
    body = _rewrite(client, rec_id).json()

    assert [r["title"] for r in body["revisions"]] == ["Take me forward", "Second"]
    assert body["title"] == "Third"


def test_the_comments_reach_the_rewrite_prompt(tmp_path):
    """Test 10: the comments are the point — they hold what the corpus does not."""
    client, _workstreams_dir, stub, rec_id = _generate_one(tmp_path)
    _patch(client, rec_id, {"comment": "HKMA's TSP means our data consumer."})
    _patch(client, rec_id, {"comment": "Scope is banking participants only."})
    accepted = _get(client).json()["recommendations"][0]["evidence"][0][
        "finding_id"
    ]
    stub.payload = {"recommendations": [_rec([accepted])]}

    _rewrite(client, rec_id)

    call = stub.calls[-1]
    prompt = recommendations.build_rewrite_prompt(
        call["rewrite_of"], call["evidence"], call["guardrails_body"]
    )
    assert "HKMA's TSP means our data consumer." in prompt
    assert "Scope is banking participants only." in prompt
    assert "Take me forward" in prompt  # the card as it stands


def test_the_guardrails_reach_the_rewrite_prompt(tmp_path):
    """Test 11: a rule she records applies to a rewrite immediately."""
    client, workstreams_dir, stub, rec_id = _generate_one(tmp_path)
    guardrails.save(workstreams_dir, _WS, "Never cite by provision number.")
    accepted = _get(client).json()["recommendations"][0]["evidence"][0][
        "finding_id"
    ]
    stub.payload = {"recommendations": [_rec([accepted])]}

    _rewrite(client, rec_id)

    assert "Never cite by provision number." in stub.calls[-1]["guardrails_body"]


def test_a_rewrite_without_a_comment_is_allowed(tmp_path):
    """Test 12: she may rewrite from evidence and guardrails alone."""
    client, _workstreams_dir, stub, rec_id = _generate_one(tmp_path)
    accepted = _get(client).json()["recommendations"][0]["evidence"][0][
        "finding_id"
    ]
    stub.payload = {"recommendations": [_rec([accepted], title="No comment needed")]}

    response = _rewrite(client, rec_id)

    assert response.status_code == 200
    assert response.json()["title"] == "No comment needed"


def test_a_rewrite_that_resolves_no_citations_is_rejected(tmp_path):
    """Test 13: a rewrite may never launder a card past the citation rule."""
    client, workstreams_dir, stub, rec_id = _generate_one(tmp_path)
    path = recommendations.recommendations_path(workstreams_dir, _WS, _TASK)
    before = path.read_bytes()

    stub.payload = {"recommendations": [_rec(["does-not-exist"])]}
    response = _rewrite(client, rec_id)

    assert response.status_code == 502
    assert response.json()["code"] == "REWRITE_FAILED"
    assert path.read_bytes() == before


def test_a_failed_rewrite_preserves_the_comment(tmp_path):
    """Test 14."""
    client, _workstreams_dir, stub, rec_id = _generate_one(tmp_path)
    _patch(client, rec_id, {"comment": "Do not lose me."})

    stub.raise_with = RuntimeError("model unavailable")
    response = _rewrite(client, rec_id)

    assert response.status_code == 502
    served = _get(client).json()["recommendations"][0]
    assert [c["text"] for c in served["comments"]] == ["Do not lose me."]
    assert served["title"] == "Take me forward"
    assert served["revisions"] == []


def test_a_rewrite_touches_only_its_own_card(tmp_path):
    """Test 15."""
    stub = _StubGenerator()
    client, workstreams_dir, stub = _make_client(tmp_path, stub)
    accepted = _accept(workstreams_dir, _HKMA_EDGE, 0)
    stub.payload = {
        "recommendations": [
            _rec([accepted], title="One"),
            _rec([accepted], title="Two"),
            _rec([accepted], title="Three"),
        ]
    }
    cards = _gen(client).json()["recommendations"]
    others = [c for c in cards if c["title"] != "One"]

    stub.payload = {"recommendations": [_rec([accepted], title="One rewritten")]}
    _rewrite(client, cards[0]["id"])

    after = _get(client).json()["recommendations"]
    assert [c["title"] for c in after] == ["One rewritten", "Two", "Three"]
    for original in others:
        assert original in after


def test_rewriting_an_unknown_recommendation_is_a_404(tmp_path):
    """Test 19."""
    client, _workstreams_dir, _stub, _rec_id = _generate_one(tmp_path)

    response = _rewrite(client, "deadbeef0000")

    assert response.status_code == 404
    assert response.json()["code"] == "RECOMMENDATION_NOT_FOUND"


def test_a_comment_does_not_survive_its_cards_replacement(tmp_path):
    """Test 17: an unbookmarked card's comments go with it. What persists is what
    the drafter put in the guardrails."""
    client, workstreams_dir, stub, rec_id = _generate_one(tmp_path)
    _patch(client, rec_id, {"comment": "Situated note."})
    accepted = _accept(workstreams_dir, _HKMA_EDGE, 1)

    stub.payload = {"recommendations": [_rec([accepted], title="Fresh set")]}
    _gen(client)

    served = _get(client).json()["recommendations"]
    assert [c["title"] for c in served] == ["Fresh set"]
    assert served[0]["comments"] == []


def test_a_bookmarked_card_keeps_its_comments_across_regeneration(tmp_path):
    """Test 18."""
    client, workstreams_dir, stub, rec_id = _generate_one(tmp_path)
    _patch(client, rec_id, {"bookmarked": True, "comment": "Keep me too."})
    accepted = _accept(workstreams_dir, _HKMA_EDGE, 1)

    stub.payload = {"recommendations": [_rec([accepted], title="Fresh")]}
    _gen(client)

    pinned = next(
        c for c in _get(client).json()["recommendations"] if c["id"] == rec_id
    )
    assert [c["text"] for c in pinned["comments"]] == ["Keep me too."]
