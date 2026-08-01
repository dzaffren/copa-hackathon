"""Tests for the source-PDF route (GET /nodes/{node_id}/source-pdf).

The Review Linkages panes offer a Source PDF button so the drafter can check a
pane's verbatim clause text against the published document it was quoted from.
This route serves that file.

Each test copies the seeded `data/workstreams/` fixtures into a `tmp_path`, so
the happy-path tests double as integrity checks on the real demo data — a
`source_pdf` pointing at a file that is not in `data/corpus/` fails here.
"""

import json
import shutil

from fastapi.testclient import TestClient

from engine.api import create_app
from engine.config import REPO_ROOT

_WS = "open-finance-pd-2026"  # the live demo workstream — the only one with PDFs
_ED = "ed-open-finance-2025"  # carries source_pdf
_TASK = "open-finance-pd-2026-pd"  # a working draft: no published PDF
_RMIT_EDGE = "e-rmit_2025--ed_open_finance_2025"  # analysed; PDFs on both sides

_OPRES = "opres-v2"  # retired fixture: no source_pdf anywhere
_BCBS_EDGE = "e-opres_v0_3--bcbs_opres_2021"


def _make_client(tmp_path, corpus_dir=None) -> tuple[TestClient, "object"]:
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    app = create_app(
        workstreams_dir=dst,
        corpus_dir=corpus_dir or REPO_ROOT / "data" / "corpus",
    )
    return TestClient(app), dst


def _pdf(client, node_id=_ED, workstream=_WS):
    return client.get(f"/api/workstreams/{workstream}/nodes/{node_id}/source-pdf")


# --- serving the file ------------------------------------------------------


def test_GET_source_pdf_serves_the_document_as_an_inline_pdf(tmp_path):
    client, _ = _make_client(tmp_path)
    res = _pdf(client)

    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    # Inline, not an attachment: the button opens the browser's viewer in a new
    # tab rather than triggering a download.
    assert "inline" in res.headers["content-disposition"]
    assert res.content.startswith(b"%PDF")


def test_GET_source_pdf_serves_every_node_that_claims_one(tmp_path):
    """Integrity check on the live fixture: a `source_pdf` that does not resolve
    to a real file under the corpus would 404 here rather than on demo day."""
    client, dst = _make_client(tmp_path)
    graph = json.loads((dst / _WS / "graph.json").read_text(encoding="utf-8"))
    claimed = [n["id"] for n in graph["nodes"] if n.get("source_pdf")]

    assert len(claimed) == 5, "the live workstream's five documents each have a PDF"
    for node_id in claimed:
        res = _pdf(client, node_id=node_id)
        assert res.status_code == 200, f"{node_id} claims a source_pdf it cannot serve"
        assert res.content.startswith(b"%PDF")


# --- nothing to serve -----------------------------------------------------


def test_GET_source_pdf_404_SOURCE_PDF_NOT_FOUND_for_a_working_draft(tmp_path):
    """A draft under active editing has no published PDF, and carries no field.
    That is an absence, not a broken pointer."""
    client, _ = _make_client(tmp_path)
    res = _pdf(client, node_id=_TASK)
    assert res.status_code == 404
    assert res.json()["code"] == "SOURCE_PDF_NOT_FOUND"


def test_GET_source_pdf_404_when_the_field_points_at_a_missing_file(tmp_path):
    client, dst = _make_client(tmp_path)
    graph_path = dst / _WS / "graph.json"
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    for node in graph["nodes"]:
        if node["id"] == _ED:
            node["source_pdf"] = "open-finance/does-not-exist.pdf"
    graph_path.write_text(json.dumps(graph), encoding="utf-8")

    res = _pdf(client)
    assert res.status_code == 404
    assert res.json()["code"] == "SOURCE_PDF_NOT_FOUND"


def test_GET_source_pdf_404_on_unknown_node(tmp_path):
    client, _ = _make_client(tmp_path)
    res = _pdf(client, node_id="nope")
    assert res.status_code == 404
    assert res.json()["code"] == "NODE_NOT_FOUND"


def test_GET_source_pdf_404_on_unknown_workstream(tmp_path):
    client, _ = _make_client(tmp_path)
    res = _pdf(client, workstream="nope")
    assert res.status_code == 404
    assert res.json()["code"] == "WORKSTREAM_NOT_FOUND"


# --- the corpus root is the boundary --------------------------------------


def test_GET_source_pdf_refuses_a_path_that_escapes_the_corpus_root(tmp_path):
    """`source_pdf` is fixture data today, but this route must not become a
    general file-read primitive over the repo. An escaping path reports the same
    404 as a missing one, so the response never confirms what lies outside."""
    secret = tmp_path / "secret.pdf"
    secret.write_bytes(b"%PDF-1.4 not yours")
    corpus = tmp_path / "corpus"
    corpus.mkdir()

    client, dst = _make_client(tmp_path, corpus_dir=corpus)
    graph_path = dst / _WS / "graph.json"
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    for node in graph["nodes"]:
        if node["id"] == _ED:
            node["source_pdf"] = "../secret.pdf"
    graph_path.write_text(json.dumps(graph), encoding="utf-8")

    res = _pdf(client)
    assert res.status_code == 404
    assert res.json()["code"] == "SOURCE_PDF_NOT_FOUND"
    assert b"not yours" not in res.content


def test_GET_source_pdf_refuses_an_absolute_path(tmp_path):
    """An absolute `source_pdf` would sidestep the root on a naive join."""
    secret = tmp_path / "secret.pdf"
    secret.write_bytes(b"%PDF-1.4 not yours")
    corpus = tmp_path / "corpus"
    corpus.mkdir()

    client, dst = _make_client(tmp_path, corpus_dir=corpus)
    graph_path = dst / _WS / "graph.json"
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    for node in graph["nodes"]:
        if node["id"] == _ED:
            node["source_pdf"] = str(secret)
    graph_path.write_text(json.dumps(graph), encoding="utf-8")

    res = _pdf(client)
    assert res.status_code == 404
    assert res.json()["code"] == "SOURCE_PDF_NOT_FOUND"
    assert b"not yours" not in res.content


# --- the review route's has_source_pdf flags -------------------------------


def test_GET_review_reports_has_source_pdf_on_both_pane_nodes(tmp_path):
    """The panes read this to decide whether to offer the button, so both sides
    must carry it."""
    client, _ = _make_client(tmp_path)
    edge = client.get(f"/api/workstreams/{_WS}/edges/{_RMIT_EDGE}/review").json()["edge"]

    assert edge["source_node"]["has_source_pdf"] is True
    assert edge["target_node"]["has_source_pdf"] is True


def test_GET_review_has_source_pdf_is_false_when_no_node_carries_one(tmp_path):
    """A retired fixture ships no `source_pdf` — the panes render without the
    button rather than offering a link that 404s."""
    client, _ = _make_client(tmp_path)
    edge = client.get(
        f"/api/workstreams/{_OPRES}/edges/{_BCBS_EDGE}/review"
    ).json()["edge"]

    assert edge["source_node"]["has_source_pdf"] is False
    assert edge["target_node"]["has_source_pdf"] is False
