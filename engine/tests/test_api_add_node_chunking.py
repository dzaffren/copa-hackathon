"""Tests for add-node with document chunking (POST /api/workstreams/{id}/nodes).

The route takes `multipart/form-data`: a JSON `payload` part carrying the node
fields (incl. the drafter's chosen `doc_class`) plus a single `attachment` file
part. On success it ingests the attachment to markdown, segments it with the
chosen strategy, persists the anchors per-node, and stamps the node with a
`document_id` and a recent-activity trail.

Ingest is stubbed with the `_FakeConverter` pattern from `test_ingest.py` — no
network, no Azure credentials. Every failure path must leave `graph.json`
untouched: no half-formed node.
"""

import json
import shutil

from fastapi.testclient import TestClient

from engine import workstreams, ws_anchors
from engine.api import create_app
from engine.config import REPO_ROOT

_OPRES = "opres-v2"
_TASK = "opres-pd-v0-3"

# Markdown the semi-structured segmenter breaks into numbered leaf sections.
SEMI_MD = """# Principles for operational resilience

1.1 A bank should establish a governance framework for operational resilience
that is approved by the board and reviewed at least annually against the
bank's risk appetite and the criticality of its operations.

1.2 A bank should identify and map its critical operations, the people,
processes, technology and third parties that support them, and the tolerance
for disruption of each of those critical operations.

1.3 A bank should conduct scenario testing of its operational resilience
arrangements against severe but plausible scenarios at least annually and
report the outcomes to the board.
"""

# Prose with no headings/numbering the semi-structured walker can anchor on.
NO_ANCHORS_MD = "   \n\n   \n"


class _FakeResult:
    def __init__(self, text: str) -> None:
        self.text_content = text


class _FakeConverter:
    """Stands in for MarkItDown/Document Intelligence — returns canned markdown."""

    def __init__(self, text: str) -> None:
        self._text = text
        self.converted: list[str] = []

    def convert(self, path: str) -> _FakeResult:
        self.converted.append(path)
        return _FakeResult(self._text)


def _client(tmp_path, markdown: str = SEMI_MD):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    # artifacts_dir is redirected too (it holds the clause/anchor indexes); the
    # committed store must gain nothing from a test run.
    app = create_app(
        workstreams_dir=dst,
        artifacts_dir=tmp_path / "artifacts",
        converter=_FakeConverter(markdown),
    )
    return TestClient(app), dst


def _graph(dst, workstream=_OPRES) -> dict:
    return json.loads((dst / workstream / "graph.json").read_text(encoding="utf-8"))


def _payload(**overrides) -> dict:
    body = {
        "node_type": "international-standard",
        "title": "BCBS Principles for Operational Resilience 2021",
        "description": "Basel Committee principles paper, 2021.",
        "doc_class": "semi-structured",
        "edges": [{"target_node_id": _TASK, "edge_type": "references"}],
    }
    body.update(overrides)
    return body


def _post(client, payload: dict, attach: bool = True):
    files = (
        {"attachment": ("bcbs-opres-2021.pdf", b"%PDF-1.7 fake", "application/pdf")}
        if attach
        else None
    )
    return client.post(
        f"/api/workstreams/{_OPRES}/nodes",
        data={"payload": json.dumps(payload)},
        files=files,
    )


# --- Happy path -------------------------------------------------------------


def test_semi_structured_attachment_produces_a_chunked_node(tmp_path):
    client, dst = _client(tmp_path)
    before = len(_graph(dst)["nodes"])

    res = _post(client, _payload())

    assert res.status_code == 201, res.text
    body = res.json()
    node_id = body["id"]
    assert body["document_id"] == node_id
    assert body["doc_class"] == "semi-structured"
    assert body["anchor_count"] > 0

    anchors = ws_anchors.load(dst, _OPRES, node_id)
    assert len(anchors) == body["anchor_count"]
    assert all(a["document_id"] == node_id for a in anchors)
    assert all(a["doc_class"] == "semi-structured" for a in anchors)

    graph = _graph(dst)
    assert len(graph["nodes"]) == before + 1
    node = next(n for n in graph["nodes"] if n["id"] == node_id)
    assert node["document_id"] == node_id


def test_anchor_text_is_verbatim_from_the_ingested_markdown(tmp_path):
    """The route must never rewrite anchor text — every passage is a literal
    substring of the source markdown."""
    client, dst = _client(tmp_path)
    node_id = _post(client, _payload()).json()["id"]

    for anchor in ws_anchors.load(dst, _OPRES, node_id):
        assert anchor["text"] in SEMI_MD


def test_recent_activity_records_creation_then_chunking(tmp_path):
    client, dst = _client(tmp_path)
    node_id = _post(client, _payload()).json()["id"]

    node = next(n for n in _graph(dst)["nodes"] if n["id"] == node_id)
    events = [entry["event"] for entry in node["recent_activity"]]
    assert events == ["node created", "chunking completed"]
    assert all(entry["at"].endswith("Z") for entry in node["recent_activity"])


def test_the_declared_edge_is_created(tmp_path):
    client, dst = _client(tmp_path)
    body = _post(client, _payload()).json()

    assert len(body["created_edges"]) == 1
    edge = body["created_edges"][0]
    # add_node's task-is-source convention: the task node stays the edge source.
    assert edge["source"] == _TASK
    assert edge["target"] == body["id"]
    assert edge["edge_type"] == "references"
    assert edge["analysed"] is False


def test_no_concepts_are_extracted_on_add(tmp_path):
    """Concept extraction is a separate, explicit story — adding a document
    only chunks it."""
    client, dst = _client(tmp_path)
    node_id = _post(client, _payload()).json()["id"]

    assert not (dst / _OPRES / "axes").exists()
    detail = client.get(f"/api/workstreams/{_OPRES}/nodes/{node_id}").json()
    assert detail["concepts"] == {"status": "not_extracted", "axes": []}


# --- Failure paths: every one leaves graph.json untouched -------------------


def test_structured_rules_runs_on_any_numbered_document(tmp_path):
    """POLICY_SHORT_NAMES is a citation-prefix convenience, not a gate: a node id
    comes from the drafter's title (never a corpus key), so gating on the table
    made the method they picked always fail. The clause regex needs nothing from
    it — the prefix is derived from the id."""
    client, dst = _client(tmp_path)

    res = _post(client, _payload(doc_class="structured-rules"))

    assert res.status_code == 201, res.text
    body = res.json()
    assert body["doc_class"] == "structured-rules"
    assert body["anchor_count"] > 0
    anchors = ws_anchors.load(dst, _OPRES, body["id"])
    # The derived prefix leads every citation, so ids stay readable.
    assert all(a["doc_class"] == "structured-rules" for a in anchors)


def test_a_document_with_no_numbered_clauses_yields_no_passages(tmp_path):
    """structured-rules on prose finds nothing to cite — reported as
    NO_PASSAGES rather than a half-formed node."""
    client, dst = _client(tmp_path, markdown="Just flowing prose, no numbering.")
    before = _graph(dst)

    res = _post(client, _payload(doc_class="structured-rules"))

    assert res.status_code == 422
    assert res.json()["code"] == "NO_PASSAGES"
    assert _graph(dst) == before


def test_a_document_that_yields_no_passages_is_rejected(tmp_path):
    client, dst = _client(tmp_path, markdown="Nothing but a sentence, no headings.")
    before = _graph(dst)

    res = _post(client, _payload())

    assert res.status_code == 422
    assert res.json()["code"] == "NO_PASSAGES"
    assert _graph(dst) == before


def test_a_missing_attachment_is_rejected(tmp_path):
    client, dst = _client(tmp_path)
    before = _graph(dst)

    res = _post(client, _payload(), attach=False)

    assert res.status_code == 400
    body = res.json()
    assert body["code"] == "ATTACHMENT_REQUIRED"
    assert body["field"] == "attachment"
    assert _graph(dst) == before


def test_an_invalid_doc_class_is_rejected_before_ingest(tmp_path):
    client, dst = _client(tmp_path)
    before = _graph(dst)

    res = _post(client, _payload(doc_class="auto"))

    assert res.status_code == 400
    body = res.json()
    assert body["code"] == "INVALID_DOC_CLASS"
    assert body["field"] == "doc_class"
    assert _graph(dst) == before


def test_a_missing_doc_class_is_rejected(tmp_path):
    client, dst = _client(tmp_path)
    payload = _payload()
    del payload["doc_class"]

    res = _post(client, payload)

    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_DOC_CLASS"


def test_an_unreadable_attachment_is_rejected(tmp_path):
    """Whitespace-only conversion output raises UnreadableDocumentError."""
    client, dst = _client(tmp_path, markdown="   \n  \n")
    before = _graph(dst)

    res = _post(client, _payload())

    assert res.status_code == 422
    body = res.json()
    assert body["code"] == "INGEST_FAILED"
    assert body["field"] == "attachment"
    assert _graph(dst) == before


def test_the_edge_requirement_still_applies(tmp_path):
    client, dst = _client(tmp_path)
    before = _graph(dst)

    res = _post(client, _payload(edges=[]))

    assert res.status_code == 400
    assert res.json()["code"] == "EDGE_REQUIRED"
    assert _graph(dst) == before


def test_an_unknown_edge_target_is_rejected(tmp_path):
    client, dst = _client(tmp_path)
    before = _graph(dst)

    res = _post(
        client,
        _payload(edges=[{"target_node_id": "nope", "edge_type": "references"}]),
    )

    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_EDGE_TARGET"
    assert _graph(dst) == before


def test_an_unknown_workstream_is_404(tmp_path):
    client, _ = _client(tmp_path)
    res = client.post(
        "/api/workstreams/nope/nodes",
        data={"payload": json.dumps(_payload())},
        files={"attachment": ("x.pdf", b"%PDF fake", "application/pdf")},
    )
    assert res.status_code == 404
    assert res.json()["code"] == "WORKSTREAM_NOT_FOUND"


def test_no_anchors_file_is_written_on_any_failure(tmp_path):
    client, dst = _client(tmp_path)
    # An invalid doc_class is refused before ingest, so nothing is persisted.
    _post(client, _payload(doc_class="auto"))
    assert not (dst / _OPRES / "anchors").exists()


def test_the_committed_stores_gain_nothing_from_a_run(tmp_path):
    """The ingested markdown and anchors land under tmp_path only — the real
    committed data/artifacts/ and data/workstreams/ must stay untouched."""
    client, dst = _client(tmp_path)
    node_id = _post(client, _payload()).json()["id"]

    assert not (REPO_ROOT / "data" / "artifacts" / f"{node_id}.md").exists()
    assert not (REPO_ROOT / "data" / "workstreams" / _OPRES / "sources").exists()
    assert not (REPO_ROOT / "data" / "workstreams" / _OPRES / "anchors").exists()
    assert ws_anchors.source_path(dst, _OPRES, node_id).exists()


def test_the_ingested_markdown_lands_beside_the_workstreams_anchors(tmp_path):
    """Per-workstream, not a flat global dir: node ids are unique only WITHIN a
    workstream, so two workstreams each adding a "RMiT 2025" would otherwise
    write the same path and clobber one another."""
    client, dst = _client(tmp_path)
    node_id = _post(client, _payload()).json()["id"]

    source = ws_anchors.source_path(dst, _OPRES, node_id)
    assert source.exists()
    assert source == dst / _OPRES / "sources" / f"{node_id}.md"
    assert source.read_text(encoding="utf-8") == SEMI_MD
    # Nothing lands in the flat artifacts dir any more.
    assert not (tmp_path / "artifacts" / f"{node_id}.md").exists()


# --- task_type: the deliverable kind of a working draft ---------------------
# A drafter can add a SECOND working draft to a workstream that already has one
# (an engagement deck accompanying a policy document), and the one question
# asked of it that is never asked of a context document is what KIND of
# deliverable it is. The answer lands on the node in graph.json, not the
# concepts side-file: like `node_type` it is structural and written once.

_TASK_NODE = {
    "node_type": "task",
    "task_type": "DECK",
    "title": "OpRes Industry Briefing",
    "description": "Slides for the 14 August industry engagement session.",
}


def test_a_task_node_is_created_with_its_deliverable_kind(tmp_path):
    client, dst = _client(tmp_path)

    res = _post(client, _payload(**_TASK_NODE))

    assert res.status_code == 201, res.text
    body = res.json()
    assert body["task_type"] == "DECK"
    node = next(n for n in _graph(dst)["nodes"] if n["id"] == body["id"])
    assert node["task_type"] == "DECK"


def test_a_task_node_without_a_deliverable_kind_is_refused(tmp_path):
    """The add-node form refuses a working draft with no kind the same way it
    refuses one with no title — and, like every other failure on this route,
    leaves graph.json untouched."""
    client, dst = _client(tmp_path)
    payload = _payload(**_TASK_NODE)
    del payload["task_type"]
    before = _graph(dst)

    res = _post(client, payload)

    assert res.status_code == 400
    body = res.json()
    assert body["code"] == "INVALID_TASK_TYPE"
    assert body["field"] == "task_type"
    assert body["message"] == "Choose what kind of deliverable this is."
    assert _graph(dst) == before


def test_an_out_of_vocabulary_deliverable_kind_is_refused(tmp_path):
    """The eight kinds are a closed set — a kind outside it is as invalid as
    none at all, so a typo cannot invent a ninth."""
    client, dst = _client(tmp_path)
    before = _graph(dst)

    res = _post(client, _payload(**{**_TASK_NODE, "task_type": "Manifesto"}))

    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_TASK_TYPE"
    assert _graph(dst) == before


def test_a_context_document_carrying_a_deliverable_kind_is_refused(tmp_path):
    """A standard is not a deliverable Aisyah is producing. Refused rather than
    silently dropped: a client sending one has misunderstood the contract, and
    swallowing it hides that until someone wonders where the kind went."""
    client, dst = _client(tmp_path)
    before = _graph(dst)

    res = _post(client, _payload(task_type="PD"))

    assert res.status_code == 400
    body = res.json()
    assert body["code"] == "TASK_TYPE_NOT_ALLOWED"
    assert body["field"] == "task_type"
    assert _graph(dst) == before


def test_a_context_document_without_one_is_still_accepted(tmp_path):
    """The unchanged majority path. `not in` rather than `is None`: absent means
    absent on disk, the fixtures' convention for `issuer` and `pursuant_to`, and
    an explicit null would read as a kind someone failed to fill in."""
    client, dst = _client(tmp_path)

    res = _post(client, _payload())

    assert res.status_code == 201, res.text
    assert res.json()["task_type"] is None
    node = next(n for n in _graph(dst)["nodes"] if n["id"] == res.json()["id"])
    assert "task_type" not in node


def test_an_invalid_node_type_is_reported_before_a_missing_kind():
    """Order is the contract: `validate_node_create` names the TOPMOST problem
    on the form, and node type sits above task type on it. A body broken in both
    places must not send the drafter to the second control first."""
    problem = workstreams.validate_node_create(
        {
            "node_type": "working-draft",  # not one of the eight
            "title": "OpRes Industry Briefing",
            "edges": [{"target_node_id": _TASK, "edge_type": "references"}],
        }
    )

    assert problem is not None
    assert problem[1] == "INVALID_NODE_TYPE"


def test_node_detail_projects_the_recorded_deliverable_kind(tmp_path):
    """The round trip the drafter performs: add the deck, then open it. The
    detail panel renders the chip from this key."""
    client, _ = _client(tmp_path)
    node_id = _post(client, _payload(**_TASK_NODE)).json()["id"]

    detail = client.get(f"/api/workstreams/{_OPRES}/nodes/{node_id}").json()

    assert detail["node_type"] == "task"
    assert detail["task_type"] == "DECK"


def test_two_workstreams_can_add_the_same_titled_document(tmp_path):
    """The collision the flat layout allowed: identical titles in different
    workstreams derive the same node id, so their sources must not share a path."""
    client, dst = _client(tmp_path)
    other = "rmit-v2-2025"

    a = _post(client, _payload()).json()["id"]
    b = client.post(
        f"/api/workstreams/{other}/nodes",
        data={
            "payload": json.dumps(
                {
                    **_payload(),
                    "edges": [
                        {"target_node_id": "rmit-pd-v2", "edge_type": "references"}
                    ],
                }
            )
        },
        files={"attachment": ("x.pdf", b"%PDF fake", "application/pdf")},
    ).json()["id"]

    assert a == b  # same title -> same node id in each workstream
    # ...but each workstream keeps its own copy.
    assert ws_anchors.source_path(dst, _OPRES, a).exists()
    assert ws_anchors.source_path(dst, other, b).exists()
    assert ws_anchors.source_path(dst, _OPRES, a) != ws_anchors.source_path(
        dst, other, b
    )
