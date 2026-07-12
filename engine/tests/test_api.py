"""Tests for engine.api — the FastAPI read service (spec Task 6 / API Design).

Covers the spec's API Design + error table at the API layer
(docs/specs/rulebook-radar/spec-knowledge-graph-engine.md, "API Design"):

- ``GET /clauses/{n}``: verbatim 200 (leaf), parent-with-``full_text`` 200,
  ``?version=`` 200, 404 CLAUSE_NOT_FOUND, 404 CLAUSE_VERSION_NOT_FOUND
  (spec Tests 1, 4, 9 at the API layer).
- ``GET /graph`` 200; ``GET /nodes/{id}`` 200 + 404 NODE_NOT_FOUND.
- ``POST /connections/find``: 200 with stubbed finder/critic reproducing the
  RMiT 17.1 ↔ Outsourcing 12.1 conflict verbatim; 400 INVALID_DOCUMENT_IDS
  (three ids, unknown id) (spec Test 6 at the API layer).
- ``POST /submissions``: 201 (supervisor + PDF, stub converter), 403 (no
  role), 415 (wrong mime), 422 (unreadable); submission text never in the
  public artifacts (spec Tests 10, 11 at the API layer).
- ``GET /submissions/{id}``: 200 with role, 403 without, 404
  SUBMISSION_NOT_FOUND.

No network / credentials / real artifacts: ``create_app`` is built from a
hand-made ``ClauseIndex`` + graph (mirroring engine/tests/test_graph.py and
test_connections.py), stubbed finder/critic and converter, and a tmp
submissions/trace dir — the cleanest testable seam.
"""

import json

from fastapi.testclient import TestClient

from engine.api import create_app
from engine.clauses import (
    ClauseIndex,
    build_clause_index,
    build_reference_clause,
    merge_clause_indexes,
)
from engine.graph import build_graph
from engine.ingest import UnreadableDocumentError

# --- Corpus fixtures (verbatim markdown + hand-written anchors) -------------

RMIT_V1_MARKDOWN = """RMiT

17 Cloud services

17.1 A financial institution shall consult the Bank prior to the first-time adoption of a public cloud service for a critical system.
"""

RMIT_V1_ANCHORS = [
    {
        "clause_number": "17.1",
        "starts_with": "A financial institution shall consult the Bank prior",
        "heading": "17 Cloud services",
        "parent": None,
    },
]

RMIT_V2_MARKDOWN = """RMiT — Exposure Draft v2

10 Technology Operations Management

10.50 A financial institution must fully understand the inherent risk of adopting cloud services.

17 Cloud services

17.1 A financial institution shall notify the Bank within 14 days of the first-time adoption of a public cloud service for a critical system, having first:
(a) completed the risk assessment under paragraph 10.50;
(b) a senior management and board readiness confirmation; and
(c) an independent third-party pre-implementation review.

17.2 A financial institution shall notify the Bank of any subsequent adoption of a public cloud service for a critical system.
"""

RMIT_V2_ANCHORS: list[dict] = [
    {
        "clause_number": "10.50",
        "starts_with": "A financial institution must fully understand the inherent risk",
        "heading": "10 Technology Operations Management",
        "parent": None,
    },
    {
        "clause_number": "17.1",
        "starts_with": "A financial institution shall notify the Bank within 14 days",
        "heading": "17 Cloud services",
        "parent": None,
    },
    {
        "clause_number": "17.1(a)",
        "starts_with": "completed the risk assessment under paragraph 10.50",
        "heading": "17 Cloud services",
        "parent": "17.1",
    },
    {
        "clause_number": "17.1(b)",
        "starts_with": "a senior management and board readiness confirmation",
        "heading": "17 Cloud services",
        "parent": "17.1",
    },
    {
        "clause_number": "17.1(c)",
        "starts_with": "an independent third-party pre-implementation review",
        "heading": "17 Cloud services",
        "parent": "17.1",
    },
    {
        "clause_number": "17.2",
        "starts_with": "A financial institution shall notify the Bank of any subsequent",
        "heading": "17 Cloud services",
        "parent": None,
    },
]

OUTSOURCING_MARKDOWN = """Outsourcing

12 Approval for material outsourcing arrangements

12.1 A financial institution must obtain the Bank's written approval before entering into a new material outsourcing arrangement.

12.4 The approval requirement does not apply to an outsourcing arrangement with an affiliate within the same financial group.
"""

OUTSOURCING_ANCHORS = [
    {
        "clause_number": "12.1",
        "starts_with": "A financial institution must obtain the Bank's written approval",
        "heading": "12 Approval for material outsourcing arrangements",
        "parent": None,
    },
    {
        "clause_number": "12.4",
        "starts_with": "The approval requirement does not apply to an outsourcing arrangement",
        "heading": "12 Approval for material outsourcing arrangements",
        "parent": None,
    },
]

OUTSOURCING_12_1_TEXT = (
    "A financial institution must obtain the Bank's written approval before "
    "entering into a new material outsourcing arrangement."
)


DOCUMENTS = {
    "rmit-v1-2020": {
        "policy_id": "rmit",
        "document_id": "rmit-v1-2020",
        "title": "Risk Management in Technology (RMiT)",
        "version": "v1 · 2020",
        "cluster": "technology-risk",
    },
    "rmit-v2-2026-draft": {
        "policy_id": "rmit",
        "document_id": "rmit-v2-2026-draft",
        "title": "Risk Management in Technology (RMiT)",
        "version": "v2 · 2026 draft",
        "cluster": "technology-risk",
    },
    "outsourcing-v1-2019": {
        "policy_id": "outsourcing",
        "document_id": "outsourcing-v1-2019",
        "title": "Outsourcing",
        "version": "v1 · 2019",
        "cluster": "technology-risk",
    },
}

DRAFT_REGISTRY = {"live_drafts": ["rmit"]}

CURATED_EDGES = [
    {
        "source_policy_id": "rmit",
        "target_policy_id": "outsourcing",
        "type": "overlaps",
        "reason": (
            "A public-cloud arrangement is often also a material outsourcing. "
            "RMiT 17.1 interacts with Outsourcing 12.1."
        ),
        "source_clauses": ["RMiT 17.1"],
        "target_clauses": ["Outsourcing 12.1"],
        "provenance": "curated",
        "confidence": 1.0,
    },
]


def _build_fixture_clause_index() -> ClauseIndex:
    rmit_v1_entries = build_clause_index(
        anchors=RMIT_V1_ANCHORS,
        markdown=RMIT_V1_MARKDOWN,
        document_id="rmit-v1-2020",
        policy_id="rmit",
        source="published",
    )
    rmit_v2_entries = build_clause_index(
        anchors=RMIT_V2_ANCHORS,
        markdown=RMIT_V2_MARKDOWN,
        document_id="rmit-v2-2026-draft",
        policy_id="rmit",
        source="draft",
    )
    outsourcing_entries = build_clause_index(
        anchors=OUTSOURCING_ANCHORS,
        markdown=OUTSOURCING_MARKDOWN,
        document_id="outsourcing-v1-2019",
        policy_id="outsourcing",
        source="published",
    )
    rmit_primary, rmit_versions = merge_clause_indexes(
        [
            ("rmit-v1-2020", rmit_v1_entries),
            ("rmit-v2-2026-draft", rmit_v2_entries),
        ],
        current_document_id="rmit-v2-2026-draft",
    )
    out_primary, out_versions = merge_clause_indexes(
        [("outsourcing-v1-2019", outsourcing_entries)],
        current_document_id="outsourcing-v1-2019",
    )
    primary = {**rmit_primary, **out_primary}
    versions = {**rmit_versions, **out_versions}
    return ClauseIndex(primary, versions)


def _build_fixture_graph(clause_index: ClauseIndex) -> dict:
    return build_graph(
        documents=DOCUMENTS,
        curated_edges=CURATED_EDGES,
        clause_index=clause_index,
        draft_registry=DRAFT_REGISTRY,
    )


# --- External reference fixtures (#26 Reference Radar) ----------------------

REFERENCE_PDPA_PASSAGE = (
    "A data controller may transfer any personal data of a data subject to any "
    "place outside Malaysia if— (a) there is in that place in force any law which "
    "is substantially similar to this Act..."
)

REFERENCE_DOCUMENTS = {
    "pdpa-2010": {
        "policy_id": "pdpa",
        "document_id": "pdpa-2010",
        "title": "Personal Data Protection Act 2010 (Malaysia)",
        "version": "2010 · Act 709",
        "cluster": "technology-risk",
        "kind": "reference",
        "source_type": "act",
        "access": "public",
        "preview": False,
        "source_url": "https://example.test/pdpa",
    },
    "bnm-handbook": {
        "policy_id": "bnm-handbook",
        "document_id": "bnm-handbook",
        "title": "Regulatory Handbook (BNM)",
        "version": "internal",
        "cluster": "technology-risk",
        "kind": "reference",
        "source_type": "handbook",
        "access": "restricted",
        "preview": False,
    },
}

REFERENCE_EDGES = [
    {
        "source_policy_id": "rmit",
        "target_policy_id": "pdpa",
        "type": "references",
        "reason": "A cloud region outside Malaysia engages the PDPA transfer test.",
        "source_clauses": ["RMiT 17.1"],
        "target_clauses": ["PDPA 129"],
        "provenance": "llm-found",
        "confidence": 0.9,
    },
    {
        "source_policy_id": "rmit",
        "target_policy_id": "bnm-handbook",
        "type": "references",
        "reason": "The handbook connects to this clause; content is confidential.",
        "source_clauses": ["RMiT 17.1"],
        "target_clauses": ["BNM Handbook — Cloud & Outsourcing Manual"],
        "provenance": "curated",
        "confidence": 1.0,
    },
]


def _build_reference_app() -> TestClient:
    """A TestClient whose graph carries reference nodes/edges and whose index
    carries the public PDPA reference passage (RMiT 17.1 + PDPA 129 resolve)."""
    from engine.clauses import build_reference_clause

    clause_index = _build_fixture_clause_index()
    primary = {
        entry["clause_number"]: entry
        for entry in [
            clause_index.get("RMiT 17.1"),
            clause_index.get("Outsourcing 12.1"),
        ]
        if entry is not None
    }
    versions = {cn: {e["document_id"]: e} for cn, e in primary.items()}
    for clause_number, entry in build_reference_clause(
        "pdpa-2010", "pdpa", "129", "Section 129(2)", REFERENCE_PDPA_PASSAGE
    ).items():
        primary[clause_number] = entry
        versions.setdefault(clause_number, {})[entry["document_id"]] = entry
    ref_index = ClauseIndex(primary, versions)

    graph = build_graph(
        documents={**DOCUMENTS, **REFERENCE_DOCUMENTS},
        curated_edges=[],
        clause_index=ref_index,
        draft_registry=DRAFT_REGISTRY,
        reference_edges=REFERENCE_EDGES,
    )
    return TestClient(create_app(clause_index=ref_index, graph=graph))


def test_get_graph_includes_reference_nodes_and_edges():
    client = _build_reference_app()

    response = client.get("/graph")
    assert response.status_code == 200
    body = response.json()

    nodes = {n["id"]: n for n in body["nodes"]}
    assert nodes["pdpa-2010"]["kind"] == "reference"
    assert nodes["pdpa-2010"]["source_type"] == "act"
    assert nodes["pdpa-2010"]["access"] == "public"
    assert nodes["pdpa-2010"]["source_url"] == "https://example.test/pdpa"
    assert nodes["bnm-handbook"]["access"] == "restricted"

    ref_edges = [e for e in body["edges"] if e["type"] == "references"]
    assert {e["target"] for e in ref_edges} == {"pdpa-2010", "bnm-handbook"}


def test_get_clause_returns_reference_passage_verbatim():
    client = _build_reference_app()

    response = client.get("/clauses/PDPA 129")
    assert response.status_code == 200
    body = response.json()
    assert body["clause_number"] == "PDPA 129"
    assert body["source"] == "reference"
    assert body["text"].startswith("A data controller may transfer")

    # The restricted handbook has no ingested passage — GET /clauses 404s for it.
    missing = client.get("/clauses/BNM Handbook — Cloud & Outsourcing Manual")
    assert missing.status_code == 404
    assert missing.json()["error"] == "CLAUSE_NOT_FOUND"


# --- Stub finder / critic / converter --------------------------------------


def _finder_returns_conflict(doc_a_id, doc_b_id, clause_index):
    return [
        {
            "summary": "RMiT 17.1 conflicts with Outsourcing 12.1.",
            "source_clauses": ["RMiT 17.1"],
            "target_clauses": ["Outsourcing 12.1"],
        }
    ]


def _critic_passthrough(doc_a_id, doc_b_id, clause_index, candidates):
    return candidates


CLEAN_SUBMISSION_TEXT = (
    "Meridian Bank Berhad — application to adopt a public cloud service for "
    "its core banking platform, a material outsourcing arrangement."
)


def _clean_converter(_file_path):
    return CLEAN_SUBMISSION_TEXT


def _unreadable_converter(_file_path):
    raise UnreadableDocumentError("Conversion yielded no usable text")


def _make_client(tmp_path, converter=_clean_converter):
    clause_index = _build_fixture_clause_index()
    graph = _build_fixture_graph(clause_index)
    app = create_app(
        clause_index=clause_index,
        graph=graph,
        submissions_dir=tmp_path / "submissions",
        finder_fn=_finder_returns_conflict,
        critic_fn=_critic_passthrough,
        trace_output_dir=tmp_path / "traces",
        submission_converter=converter,
    )
    return TestClient(app)


# --- GET /clauses/{n} -------------------------------------------------------


def test_get_clause_leaf_returns_verbatim_text(tmp_path):
    """Spec Test 1 at the API layer — verbatim leaf fetch."""
    client = _make_client(tmp_path)
    response = client.get("/clauses/Outsourcing%2012.1")
    assert response.status_code == 200
    body = response.json()
    assert body["clause_number"] == "Outsourcing 12.1"
    assert body["text"] == OUTSOURCING_12_1_TEXT
    assert body["source"] == "published"
    assert body["policy_id"] == "outsourcing"
    assert body["document_id"] == "outsourcing-v1-2019"
    assert "full_text" not in body
    # The private `_full_text` field never leaks into the API contract.
    assert "_full_text" not in body


def test_get_clause_parent_includes_composed_full_text(tmp_path):
    client = _make_client(tmp_path)
    response = client.get("/clauses/RMiT%2017.1")
    assert response.status_code == 200
    body = response.json()
    assert body["clause_number"] == "RMiT 17.1"
    assert body["children"] == ["RMiT 17.1(a)", "RMiT 17.1(b)", "RMiT 17.1(c)"]
    assert "full_text" in body
    assert body["full_text"].startswith(body["text"])
    assert "senior management and board readiness confirmation" in body["full_text"]
    assert "_full_text" not in body


def test_get_clause_specific_version_returns_historical_entry(tmp_path):
    """Spec Test 9 at the API layer — history via ?version=."""
    client = _make_client(tmp_path)
    response = client.get("/clauses/RMiT%2017.1?version=rmit-v1-2020")
    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == "rmit-v1-2020"
    assert body["source"] == "published"
    assert "consult the Bank prior" in body["text"]


def test_get_clause_unknown_returns_404_clause_not_found(tmp_path):
    """Spec Test 4 at the API layer — missing clause reported honestly."""
    client = _make_client(tmp_path)
    response = client.get("/clauses/Outsourcing%2099.9")
    assert response.status_code == 404
    body = response.json()
    assert body == {
        "error": "CLAUSE_NOT_FOUND",
        "message": "No matching clause found for 'Outsourcing 99.9'",
    }


def test_get_clause_unknown_version_returns_404_clause_version_not_found(tmp_path):
    client = _make_client(tmp_path)
    response = client.get("/clauses/RMiT%2017.1?version=rmit-v9")
    assert response.status_code == 404
    body = response.json()
    assert body == {
        "error": "CLAUSE_VERSION_NOT_FOUND",
        "message": "No version 'rmit-v9' for clause 'RMiT 17.1'",
    }


# --- GET /graph -------------------------------------------------------------


def test_get_graph_returns_nodes_and_edges(tmp_path):
    client = _make_client(tmp_path)
    response = client.get("/graph")
    assert response.status_code == 200
    body = response.json()
    assert "nodes" in body and "edges" in body
    node_ids = {n["id"] for n in body["nodes"]}
    assert "rmit-v2-2026-draft" in node_ids


# --- GET /nodes/{id} --------------------------------------------------------


def test_get_node_returns_status_and_incident_edges(tmp_path):
    client = _make_client(tmp_path)
    response = client.get("/nodes/rmit-v2-2026-draft")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "rmit-v2-2026-draft"
    assert body["title"] == "Risk Management in Technology (RMiT)"
    assert body["status"] == "In progress"
    targets = {e["target"] for e in body["edges"]}
    assert "outsourcing-v1-2019" in targets
    for edge in body["edges"]:
        assert set(edge.keys()) == {"target", "type", "reason"}


def test_get_node_unknown_returns_404_node_not_found(tmp_path):
    client = _make_client(tmp_path)
    response = client.get("/nodes/rmit-v9")
    assert response.status_code == 404
    assert response.json() == {
        "error": "NODE_NOT_FOUND",
        "message": "No node with id 'rmit-v9'",
    }


# --- POST /connections/find -------------------------------------------------


def test_post_connections_find_surfaces_verbatim_conflict(tmp_path):
    """Spec Test 6 at the API layer — RMiT 17.1 ↔ Outsourcing 12.1 conflict."""
    client = _make_client(tmp_path)
    response = client.post(
        "/connections/find",
        json={"document_ids": ["rmit-v2-2026-draft", "outsourcing-v1-2019"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["unsupported"] == []
    conflict = body["connections"][0]
    assert conflict["supported"] is True
    target_12_1 = next(
        tc
        for tc in conflict["target_clauses"]
        if tc["clause_number"] == "Outsourcing 12.1"
    )
    assert target_12_1["text"] == OUTSOURCING_12_1_TEXT


def test_post_connections_find_three_ids_returns_400(tmp_path):
    client = _make_client(tmp_path)
    response = client.post(
        "/connections/find",
        json={"document_ids": ["rmit-v2-2026-draft", "outsourcing-v1-2019", "x"]},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "INVALID_DOCUMENT_IDS"


def test_post_connections_find_unknown_id_returns_400(tmp_path):
    client = _make_client(tmp_path)
    response = client.post(
        "/connections/find",
        json={"document_ids": ["rmit-v2-2026-draft", "rmit-v9"]},
    )
    assert response.status_code == 400
    body = response.json()
    assert body == {
        "error": "INVALID_DOCUMENT_IDS",
        "message": "Unknown document id 'rmit-v9'",
    }


# --- POST /submissions ------------------------------------------------------

PDF_MIME = "application/pdf"
DOCX_MIME = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


def test_post_submission_supervisor_pdf_returns_201(tmp_path):
    """Spec Test 10 at the API layer — authorised ingest, isolated + tagged."""
    client = _make_client(tmp_path)
    response = client.post(
        "/submissions",
        headers={"X-Role": "supervisor"},
        files={
            "file": (
                "meridian-cloud-outsourcing-application.pdf",
                b"%PDF-1.4 fake meridian bytes",
                PDF_MIME,
            )
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["submission_id"]
    assert body["sensitivity"] == "supervised-entity-confidential"

    # Isolation: the submission text is in the submissions store only, never
    # in the served graph or any clause the API returns.
    graph_body = client.get("/graph").json()
    assert CLEAN_SUBMISSION_TEXT not in json.dumps(graph_body)


def test_post_submission_without_role_returns_403(tmp_path):
    client = _make_client(tmp_path)
    response = client.post(
        "/submissions",
        files={"file": ("x.pdf", b"%PDF-1.4", PDF_MIME)},
    )
    assert response.status_code == 403
    assert response.json() == {
        "error": "SUBMISSION_ACCESS_DENIED",
        "message": "Supervisor role required to ingest submissions",
    }
    # Zero residue: nothing landed in the submissions store on the reject path.
    submissions_dir = tmp_path / "submissions"
    if submissions_dir.exists():
        assert list(submissions_dir.iterdir()) == []


def test_post_submission_wrong_mime_returns_415(tmp_path):
    client = _make_client(tmp_path)
    response = client.post(
        "/submissions",
        headers={"X-Role": "supervisor"},
        files={"file": ("x.txt", b"plain text", "text/plain")},
    )
    assert response.status_code == 415
    assert response.json() == {
        "error": "UNSUPPORTED_FORMAT",
        "message": "Only PDF and DOCX submissions are supported",
    }
    submissions_dir = tmp_path / "submissions"
    if submissions_dir.exists():
        assert list(submissions_dir.iterdir()) == []


def test_post_submission_unreadable_returns_422(tmp_path):
    """Spec Test 11 at the API layer — unreadable rejected, zero residue."""
    client = _make_client(tmp_path, converter=_unreadable_converter)
    response = client.post(
        "/submissions",
        headers={"X-Role": "supervisor"},
        files={"file": ("scan.pdf", b"scanned image bytes", PDF_MIME)},
    )
    assert response.status_code == 422
    assert response.json() == {
        "error": "UNREADABLE_DOCUMENT",
        "message": "The document could not be read; no text was stored",
    }
    submissions_dir = tmp_path / "submissions"
    if submissions_dir.exists():
        assert list(submissions_dir.iterdir()) == []


# --- GET /submissions/{id} --------------------------------------------------


def test_get_submission_with_role_returns_text(tmp_path):
    client = _make_client(tmp_path)
    post = client.post(
        "/submissions",
        headers={"X-Role": "supervisor"},
        files={"file": ("meridian.pdf", b"%PDF-1.4", PDF_MIME)},
    )
    submission_id = post.json()["submission_id"]

    response = client.get(
        f"/submissions/{submission_id}", headers={"X-Role": "supervisor"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["submission_id"] == submission_id
    assert body["text"] == CLEAN_SUBMISSION_TEXT
    assert body["sensitivity"] == "supervised-entity-confidential"


def test_get_submission_without_role_returns_403(tmp_path):
    client = _make_client(tmp_path)
    post = client.post(
        "/submissions",
        headers={"X-Role": "supervisor"},
        files={"file": ("meridian.pdf", b"%PDF-1.4", PDF_MIME)},
    )
    submission_id = post.json()["submission_id"]

    response = client.get(f"/submissions/{submission_id}")
    assert response.status_code == 403
    assert response.json() == {
        "error": "SUBMISSION_ACCESS_DENIED",
        "message": "Supervisor role required to ingest submissions",
    }


def test_get_submission_unknown_id_returns_404(tmp_path):
    client = _make_client(tmp_path)
    response = client.get(
        "/submissions/sub-999", headers={"X-Role": "supervisor"}
    )
    assert response.status_code == 404
    assert response.json() == {
        "error": "SUBMISSION_NOT_FOUND",
        "message": "No submission with id 'sub-999'",
    }


# ===========================================================================
# Two-branch source-connection routes (spec Task 6): GET …/paragraphs,
# GET …/{number}/connections, POST …/{number}/analyse.
#
# Model-free reads over a hand-made clause index + graph + verdicts dict (the
# verdicts.json join); the live analyse route uses a stubbed `analyse_fn`, so no
# network — the same no-network discipline as the finder/critic tests above.
# ===========================================================================

# Verbatim source-clause text the connections quote (byte-for-byte via the index,
# never the verdict record). Reused in the fixtures AND the byte-for-byte asserts.
AIDP_PDPA_129_TEXT = (
    "A data controller may transfer any personal data of a data subject to any "
    "place outside Malaysia if— (a) there is in that place in force any law "
    "which is substantially similar to this Act."
)
AIDP_BCBS_P4_TEXT = (
    "A bank should be able to capture and aggregate all material risk data "
    "across the banking group."
)
AIDP_FSP_TEXT = (
    "The requirement to obtain informed consent is unworkable for models already "
    "trained on legacy datasets collected before AI use was contemplated."
)

# Vehicle-document (AI DP) paragraph text — the addressable analysed units.
AIDP_PARAGRAPHS = [
    ("4.6", "Data & personal information", "As AI applications process personal data..."),
    ("3.5", "Fair usage & bias", "A major challenge of AI revolves around fair usage..."),
    ("3.2", "Board & senior management oversight", "The board and senior management..."),
    ("5.2", "Capital treatment", "Capital treatment considerations for AI models..."),
]


def _aidp_paragraph_entry(number: str, heading: str, text: str) -> tuple[str, dict]:
    clause_number = f"AI-DP {number}"
    return clause_number, {
        "clause_number": clause_number,
        "policy_id": "ai-dp",
        "document_id": "ai-dp-2025",
        "text": text,
        "heading": heading,
        "source": "published",
        "parent": None,
        "children": [],
        "superseded_versions": [],
    }


def _build_aidp_clause_index() -> ClauseIndex:
    """The vehicle DP's paragraphs + the verbatim source passages the quotes come
    from (source clause text NEVER comes from the verdict record)."""
    primary: dict = {}
    for number, heading, text in AIDP_PARAGRAPHS:
        clause_number, entry = _aidp_paragraph_entry(number, heading, text)
        primary[clause_number] = entry
    for clause_number, ref_entry in {
        **build_reference_clause(
            "pdpa-2010", "pdpa", "129", "Section 129(2)", AIDP_PDPA_129_TEXT
        ),
        **build_reference_clause(
            "bcbs-239", "bcbs-239", "P4", "Principle 4", AIDP_BCBS_P4_TEXT
        ),
        **build_reference_clause(
            "industry-fsp-3", "industry-fsp-3", "FSP-3", "FSP feedback", AIDP_FSP_TEXT
        ),
    }.items():
        primary[clause_number] = ref_entry
    return ClauseIndex(primary)


def _reference_node(node_id: str, title: str, source_type: str, **extra) -> dict:
    return {
        "id": node_id,
        "policy_id": node_id,
        "title": title,
        "version": "ref",
        "status": "In force",
        "cluster": "ai-financial-sector",
        "kind": "reference",
        "source_type": source_type,
        "access": "public",
        "preview": False,
        **extra,
    }


AIDP_GRAPH = {
    "nodes": [
        {
            "id": "ai-dp-2025",
            "policy_id": "ai-dp",
            "title": "Discussion Paper on AI in the Malaysian Financial Sector",
            "version": "DP Aug 2025",
            "status": "In progress",
            "cluster": "ai-financial-sector",
            "kind": "policy",
        },
        _reference_node(
            "pdpa-2010",
            "Personal Data Protection Act 2010 (as amended 2024)",
            "act",
        ),
        _reference_node("bcbs-239", "BCBS 239", "international_standard"),
        _reference_node(
            "industry-fsp-3", "Industry feedback — 3 FSP respondents", "industry_feedback"
        ),
        _reference_node("mas-feat", "MAS — FEAT Principles (Fairness)", "peer_regulator"),
    ],
    "edges": [],
}

# verdicts.json join: 4.6 (PDPA Conflict + BCBS Consensus + FSP Partial), 3.5
# (MAS FEAT blocked), 5.2 (pending-extraction Basel row). Confidence is the band
# string the verdict stage already computed; render adds `verdict_status`.
AIDP_VERDICTS = {
    "ai-dp-2025:4.6::pdpa-2010:PDPA 129": {
        "id": "ai-dp-2025:4.6::pdpa-2010:PDPA 129",
        "paragraph": "4.6",
        "branch": "uncited",
        "source_document_id": "pdpa-2010",
        "verdict": "Conflict",
        "verdict_status": "proposed",
        "confidence": "High",
        "rationale": (
            "4.6 relies on broad informed consent; PDPA §129 sets a specific "
            "cross-border transfer test the draft does not cite."
        ),
        "clause_number": "PDPA 129",
        "verification": "verified",
    },
    "ai-dp-2025:4.6::bcbs239:BCBS 239 P4": {
        "id": "ai-dp-2025:4.6::bcbs239:BCBS 239 P4",
        "paragraph": "4.6",
        "branch": "cited",
        "source_document_id": "bcbs-239",
        "verdict": "Consensus",
        "verdict_status": "proposed",
        "confidence": "High",
        "rationale": "BCBS 239 completeness supports 4.6's governed-data expectation.",
        "clause_number": "BCBS 239 P4",
        "verification": "verified",
    },
    "ai-dp-2025:4.6::industry-fsp-3": {
        "id": "ai-dp-2025:4.6::industry-fsp-3",
        "paragraph": "4.6",
        "branch": "feedback",
        "source_document_id": "industry-fsp-3",
        "verdict": "Partial",
        "verdict_status": "proposed",
        "confidence": "Medium",
        "rationale": "Agrees on responsible handling, rejects consent for legacy data.",
        "clause_number": "Industry FSP-3",
        "verification": "illustrative",
        "stance": "partial",
    },
    "ai-dp-2025:3.5::mas-feat": {
        "id": "ai-dp-2025:3.5::mas-feat",
        "paragraph": "3.5",
        "branch": "uncited",
        "source_document_id": "mas-feat",
        "status": "could_not_retrieve",
        "reason": (
            "The MAS site blocks automated access; upload the source to analyse "
            "this connection."
        ),
        "verdict": None,
        "verdict_status": "proposed",
        "clause_number": None,
    },
    "ai-dp-2025:5.2::basel:Basel RBC20": {
        "id": "ai-dp-2025:5.2::basel:Basel RBC20",
        "paragraph": "5.2",
        "branch": "uncited",
        "source_document_id": "bcbs-239",
        "verdict": "Gap",
        "verdict_status": "proposed",
        "confidence": "Medium",
        "rationale": "Illustrative Basel row; passage not yet extracted.",
        "clause_number": "Basel RBC20",
        "verification": "pending_extraction",
    },
}


def _make_paragraph_client(
    tmp_path, analyse_fn=None, verdict_fn=None, graph=None, verdicts=None
) -> TestClient:
    app = create_app(
        clause_index=_build_aidp_clause_index(),
        graph=AIDP_GRAPH if graph is None else graph,
        submissions_dir=tmp_path / "submissions",
        verdicts=AIDP_VERDICTS if verdicts is None else verdicts,
        analyse_fn=analyse_fn,
        verdict_fn=verdict_fn,
    )
    return TestClient(app)


# --- GET /documents/{id}/paragraphs -----------------------------------------


def test_get_paragraphs_index_states_and_counts(tmp_path):
    client = _make_paragraph_client(tmp_path)
    response = client.get("/documents/ai-dp-2025/paragraphs")
    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == "ai-dp-2025"
    assert body["total_paragraphs"] == 4
    by_number = {p["number"]: p for p in body["paragraphs"]}
    assert by_number["4.6"]["state"] == "analysed"
    assert by_number["4.6"]["connection_count"] == 3
    assert by_number["4.6"]["title"] == "Data & personal information"
    assert by_number["3.2"]["state"] == "not_analysed"
    assert by_number["3.2"]["connection_count"] == 0


def test_get_paragraphs_unknown_document_returns_404(tmp_path):
    client = _make_paragraph_client(tmp_path)
    response = client.get("/documents/nope/paragraphs")
    assert response.status_code == 404
    assert response.json() == {
        "error": "DOCUMENT_NOT_FOUND",
        "message": "No document with id 'nope'",
    }


# --- GET /documents/{id}/paragraphs/{number}/connections --------------------


def test_get_paragraph_connections_4_6_full_render(tmp_path):
    """Spec Test 6 — 4.6 returns three connections, each with branch, source
    type, verdict, confidence, rationale, and a verification-marked quote."""
    client = _make_paragraph_client(tmp_path)
    response = client.get("/documents/ai-dp-2025/paragraphs/4.6/connections")
    assert response.status_code == 200
    body = response.json()
    assert body["paragraph"]["number"] == "4.6"
    assert body["state"] == "analysed"
    assert body["no_matching_source"] is False

    conns = body["connections"]
    assert len(conns) == 3
    for conn in conns:
        assert "branch" in conn
        assert "source_type" in conn["source"]
        assert "verdict" in conn
        assert "confidence" in conn
        assert "rationale" in conn
        assert conn["quote"]["verification"] in {"verified", "illustrative"}

    # The PDPA connection is a Conflict, verified, and its quote text is the
    # index text byte-for-byte — never the verdict record's rationale.
    pdpa = next(c for c in conns if c["source"]["document_id"] == "pdpa-2010")
    assert pdpa["verdict"] == "Conflict"
    assert pdpa["verdict_status"] == "proposed"
    assert pdpa["quote"]["verification"] == "verified"
    assert pdpa["quote"]["text"] == AIDP_PDPA_129_TEXT
    assert pdpa["quote"]["text"] != pdpa["rationale"]


def test_get_paragraph_connections_blocked_source(tmp_path):
    """Spec Test 7 — a blocked source (MAS FEAT) renders could_not_retrieve with
    a reason, verdict null, quote null; never a fabricated verdict/quote."""
    client = _make_paragraph_client(tmp_path)
    response = client.get("/documents/ai-dp-2025/paragraphs/3.5/connections")
    assert response.status_code == 200
    conns = response.json()["connections"]
    assert len(conns) == 1
    mas = conns[0]
    assert mas["source"]["document_id"] == "mas-feat"
    assert mas["status"] == "could_not_retrieve"
    assert mas["reason"]
    assert mas["verdict"] is None
    assert mas["quote"] is None


def test_get_paragraph_connections_pending_extraction(tmp_path):
    """Spec Test 8 — a pending-extraction connection renders quote.text null with
    a pending_extraction marker; no approximated string is returned."""
    client = _make_paragraph_client(tmp_path)
    response = client.get("/documents/ai-dp-2025/paragraphs/5.2/connections")
    assert response.status_code == 200
    conn = response.json()["connections"][0]
    assert conn["quote"]["verification"] == "pending_extraction"
    assert conn["quote"]["text"] is None  # never an approximated string


def test_get_paragraph_connections_unknown_paragraph_returns_404(tmp_path):
    client = _make_paragraph_client(tmp_path)
    response = client.get("/documents/ai-dp-2025/paragraphs/9.9/connections")
    assert response.status_code == 404
    assert response.json() == {
        "error": "PARAGRAPH_NOT_FOUND",
        "message": "No paragraph '9.9' in document 'ai-dp-2025'",
    }


def test_get_paragraph_connections_unknown_document_returns_404(tmp_path):
    client = _make_paragraph_client(tmp_path)
    response = client.get("/documents/nope/paragraphs/4.6/connections")
    assert response.status_code == 404
    assert response.json()["error"] == "DOCUMENT_NOT_FOUND"


# --- POST /documents/{id}/paragraphs/{number}/analyse -----------------------


def _empty_analyse_fn(document_id, number, paragraph_text, clause_index):
    return []


def test_post_analyse_bare_paragraph_returns_no_matching_source(tmp_path):
    """Spec Test 5 — analysing a bare paragraph (3.2) with nothing bearing on it
    returns 200 / analysed / no_matching_source, not a fabrication."""
    client = _make_paragraph_client(tmp_path, analyse_fn=_empty_analyse_fn)
    response = client.post("/documents/ai-dp-2025/paragraphs/3.2/analyse")
    assert response.status_code == 200
    body = response.json()
    assert body["paragraph"]["number"] == "3.2"
    assert body["state"] == "analysed"
    assert body["no_matching_source"] is True
    assert body["connections"] == []


def test_post_analyse_live_candidates_render(tmp_path):
    """A live analyse whose stub finder surfaces a candidate returns it rendered
    (verdict + verbatim quote) — the same shape as GET …/connections."""
    def analyse_fn(document_id, number, paragraph_text, clause_index):
        return [
            {
                "id": "ai-dp-2025:3.2::bcbs-239:BCBS 239 P4",
                "paragraph": number,
                "branch": "uncited",
                "source_document_id": "bcbs-239",
                "clause_number": "BCBS 239 P4",
                "confidence_score": 0.88,
                "verification": "verified",
                "verdict": "Consensus",
                "rationale": "BCBS 239 completeness bears on board data oversight.",
            }
        ]

    client = _make_paragraph_client(tmp_path, analyse_fn=analyse_fn)
    response = client.post("/documents/ai-dp-2025/paragraphs/3.2/analyse")
    assert response.status_code == 200
    body = response.json()
    assert body["no_matching_source"] is False
    conn = body["connections"][0]
    assert conn["verdict"] == "Consensus"
    assert conn["quote"]["text"] == AIDP_BCBS_P4_TEXT


def test_post_analyse_already_analysed_without_force_returns_400(tmp_path):
    client = _make_paragraph_client(tmp_path, analyse_fn=_empty_analyse_fn)
    response = client.post("/documents/ai-dp-2025/paragraphs/4.6/analyse")
    assert response.status_code == 400
    assert response.json() == {
        "error": "INVALID_ANALYSE_REQUEST",
        "message": (
            "Paragraph '4.6' is already analysed; re-analysis requires "
            "?force=true"
        ),
    }


def test_post_analyse_already_analysed_with_force_reanalyses(tmp_path):
    client = _make_paragraph_client(tmp_path, analyse_fn=_empty_analyse_fn)
    response = client.post(
        "/documents/ai-dp-2025/paragraphs/4.6/analyse?force=true"
    )
    assert response.status_code == 200
    assert response.json()["no_matching_source"] is True


def test_post_analyse_empty_library_returns_409(tmp_path):
    graph_no_refs = {
        "nodes": [
            {
                "id": "ai-dp-2025",
                "policy_id": "ai-dp",
                "title": "AI DP",
                "version": "v",
                "status": "In progress",
                "cluster": "ai-financial-sector",
                "kind": "policy",
            }
        ],
        "edges": [],
    }
    client = _make_paragraph_client(
        tmp_path, analyse_fn=_empty_analyse_fn, graph=graph_no_refs
    )
    response = client.post("/documents/ai-dp-2025/paragraphs/3.2/analyse")
    assert response.status_code == 409
    assert response.json()["error"] == "SOURCE_LIBRARY_EMPTY"


def test_post_analyse_seam_missing_returns_503(tmp_path):
    client = _make_paragraph_client(tmp_path)  # analyse_fn=None
    response = client.post("/documents/ai-dp-2025/paragraphs/3.2/analyse")
    assert response.status_code == 503
    assert response.json()["error"] == "ANALYSE_UNAVAILABLE"


def test_post_analyse_seam_raising_returns_503(tmp_path):
    def boom(document_id, number, paragraph_text, clause_index):
        raise RuntimeError("Azure hiccup mid-pitch")

    client = _make_paragraph_client(tmp_path, analyse_fn=boom)
    response = client.post("/documents/ai-dp-2025/paragraphs/3.2/analyse")
    assert response.status_code == 503
    assert response.json() == {
        "error": "ANALYSE_UNAVAILABLE",
        "message": (
            "Live analysis is temporarily unavailable; pre-analysed paragraphs "
            "are unaffected"
        ),
    }


def test_post_analyse_verdict_stage_failure_returns_503(tmp_path):
    """A live VERDICT-stage failure also degrades to 503 — the graceful backstop
    must cover the verdict pass, not just the finder, so a mid-pitch verdict
    hiccup (or an invalid verdict) never surfaces a raw 500."""

    def analyse_fn(document_id, number, paragraph_text, clause_index):
        # A supported candidate with NO frozen verdict → verdict_fn is invoked.
        return [
            {
                "id": "ai-dp-2025:3.2::bcbs-239:BCBS 239 P4",
                "paragraph": number,
                "branch": "uncited",
                "source_document_id": "bcbs-239",
                "clause_number": "BCBS 239 P4",
                "confidence_score": 0.88,
                "verification": "verified",
            }
        ]

    def boom_verdict(connection, clause_index):
        raise RuntimeError("verdict model timed out")

    client = _make_paragraph_client(
        tmp_path, analyse_fn=analyse_fn, verdict_fn=boom_verdict
    )
    response = client.post("/documents/ai-dp-2025/paragraphs/3.2/analyse")
    assert response.status_code == 503
    assert response.json()["error"] == "ANALYSE_UNAVAILABLE"


def test_post_analyse_unknown_paragraph_returns_404(tmp_path):
    client = _make_paragraph_client(tmp_path, analyse_fn=_empty_analyse_fn)
    response = client.post("/documents/ai-dp-2025/paragraphs/9.9/analyse")
    assert response.status_code == 404
    assert response.json()["error"] == "PARAGRAPH_NOT_FOUND"


# --- Regression guard: existing routes unchanged by the new paragraph app ----


def test_existing_routes_unchanged_on_paragraph_app(tmp_path):
    """The new verdicts/analyse params must not disturb the existing contracts:
    GET /graph and GET /clauses/{n} still respond exactly as before."""
    client = _make_paragraph_client(tmp_path)

    graph = client.get("/graph")
    assert graph.status_code == 200
    graph_body = graph.json()
    assert "nodes" in graph_body and "edges" in graph_body
    assert any(n["id"] == "pdpa-2010" for n in graph_body["nodes"])

    clause = client.get("/clauses/PDPA 129")
    assert clause.status_code == 200
    assert clause.json()["text"] == AIDP_PDPA_129_TEXT
