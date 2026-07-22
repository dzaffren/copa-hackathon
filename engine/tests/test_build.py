"""Tests for engine.build — CLI wiring of stages 1-3 (ingest -> clauses -> graph).

No network access: `ingest_fn` is stubbed with hand-written markdown; stage 2
uses the REAL deterministic `segment_clauses` (network-free, so no stub is
needed — this exercises the true segmentation path end-to-end). This proves
`build.py` is wired correctly and can run without any Foundry credentials.
"""

import json
import re

import pytest

from engine.build import AnchorCompletenessError, build_anchor_index, run_build

# Hand-written markdown in the real BNM line-start format the segmenter expects:
# a section heading ("12 Approval…"), then its numbered clause ("12.1 …").
OUTSOURCING_MARKDOWN = (
    "Outsourcing\n\n"
    "12 Approval for material outsourcing arrangements\n\n"
    "12.1 A financial institution must obtain the Bank's written approval "
    "before entering into a new material outsourcing arrangement.\n"
)

OPRES_MARKDOWN = (
    "Operational Resilience\n\n"
    "6 Critical operations\n\n"
    "6.11 A financial institution must maintain a register of critical "
    "cloud and third-party services.\n"
)

FIXTURE_DOCUMENTS = {
    "outsourcing-v1-2019": {
        "policy_id": "outsourcing",
        "document_id": "outsourcing-v1-2019",
        "title": "Outsourcing",
        "version": "v1 · 2019",
        "source_path": "outsourcing.pdf",
        "source": "published",
        "cluster": "technology-risk",
    },
    "opres-v1-2025": {
        "policy_id": "opres",
        "document_id": "opres-v1-2025",
        "title": "Operational Resilience",
        "version": "v1 · 2025",
        "source_path": "opres.pdf",
        "source": "published",
        "cluster": "technology-risk",
    },
}

FIXTURE_CURATED_EDGES = [
    {
        "source_policy_id": "outsourcing",
        "target_policy_id": "opres",
        "type": "overlaps",
        "reason": "Both concern third-party arrangements for critical services.",
        "source_clauses": ["Outsourcing 12.1"],
        "target_clauses": ["Operational Resilience 6.11"],
        "provenance": "curated",
        "confidence": 1.0,
    },
]

FIXTURE_MARKDOWN_BY_PATH = {
    "outsourcing.pdf": OUTSOURCING_MARKDOWN,
    "opres.pdf": OPRES_MARKDOWN,
}


def _stub_ingest_fn(path):
    return FIXTURE_MARKDOWN_BY_PATH[str(path)]


def test_run_build_writes_clause_index_and_graph_artifacts(tmp_path):
    output_dir = tmp_path / "artifacts"

    run_build(
        documents=FIXTURE_DOCUMENTS,
        curated_edges=FIXTURE_CURATED_EDGES,
        draft_registry={"live_drafts": ["opres"]},
        output_dir=output_dir,
        ingest_fn=_stub_ingest_fn,
    )

    clause_index_path = output_dir / "clause-index.json"
    graph_path = output_dir / "graph.json"
    assert clause_index_path.exists()
    assert graph_path.exists()

    clause_index = json.loads(clause_index_path.read_text())
    assert "Outsourcing 12.1" in clause_index
    assert clause_index["Outsourcing 12.1"]["text"].strip() == (
        "A financial institution must obtain the Bank's written approval "
        "before entering into a new material outsourcing arrangement."
    )

    graph = json.loads(graph_path.read_text())
    node_ids = {n["id"] for n in graph["nodes"]}
    assert node_ids == {"outsourcing-v1-2019", "opres-v1-2025"}
    non_lineage = [e for e in graph["edges"] if e["type"] != "version-lineage"]
    assert len(non_lineage) == 1
    assert non_lineage[0]["reason"]


FIXTURE_REFERENCE_DOCUMENTS = {
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
        "anchor": "129",
        "heading": "Section 129(2) — transfer of personal data outside Malaysia",
        "passage": (
            "A data controller may transfer any personal data of a data subject "
            "to any place outside Malaysia if— (a) there is in that place in "
            "force any law which is substantially similar to this Act..."
        ),
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

FIXTURE_REFERENCE_EDGES = [
    {
        "source_policy_id": "outsourcing",
        "target_policy_id": "pdpa",
        "type": "references",
        "reason": "Outsourcing that moves customer data offshore engages the PDPA.",
        "source_clauses": ["Outsourcing 12.1"],
        "target_clauses": ["PDPA 129"],
        "provenance": "llm-found",
        "confidence": 0.9,
    },
    {
        "source_policy_id": "outsourcing",
        "target_policy_id": "bnm-handbook",
        "type": "references",
        "reason": "The handbook connects to this clause; its content is confidential.",
        "source_clauses": ["Outsourcing 12.1"],
        "target_clauses": ["BNM Handbook — Cloud & Outsourcing Manual"],
        "provenance": "curated",
        "confidence": 1.0,
    },
]


def test_run_build_emits_reference_nodes_edges_and_public_passage(tmp_path):
    output_dir = tmp_path / "artifacts"

    run_build(
        documents=FIXTURE_DOCUMENTS,
        curated_edges=FIXTURE_CURATED_EDGES,
        draft_registry={"live_drafts": ["opres"]},
        output_dir=output_dir,
        ingest_fn=_stub_ingest_fn,
        reference_documents=FIXTURE_REFERENCE_DOCUMENTS,
        reference_edges=FIXTURE_REFERENCE_EDGES,
    )

    clause_index = json.loads(
        (output_dir / "clause-index.json").read_text(encoding="utf-8")
    )
    # The PUBLIC reference passage is in the clause index, verbatim, source="reference".
    assert "PDPA 129" in clause_index
    assert clause_index["PDPA 129"]["text"].startswith(
        "A data controller may transfer"
    )
    assert clause_index["PDPA 129"]["source"] == "reference"
    # The RESTRICTED handbook contributes NO clause (node-only — nothing ingested,
    # so there is no confidential text in any artifact to leak).
    assert not any(k.startswith("BNM Handbook") for k in clause_index)

    graph = json.loads((output_dir / "graph.json").read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in graph["nodes"]}
    assert nodes["pdpa-2010"]["kind"] == "reference"
    assert nodes["pdpa-2010"]["source_type"] == "act"
    assert nodes["pdpa-2010"]["source_url"] == "https://example.test/pdpa"
    assert nodes["bnm-handbook"]["access"] == "restricted"
    assert "source_url" not in nodes["bnm-handbook"]
    # Existing policy nodes gain kind:"policy" (backward compatible).
    assert nodes["outsourcing-v1-2019"]["kind"] == "policy"

    ref_edges = [e for e in graph["edges"] if e["type"] == "references"]
    assert {e["target"] for e in ref_edges} == {"pdpa-2010", "bnm-handbook"}
    pdpa_edge = next(e for e in ref_edges if e["target"] == "pdpa-2010")
    assert pdpa_edge["provenance"] == "llm-found"
    assert pdpa_edge["confidence"] == 0.9


# --- Vehicle-document glyph normalisation (Task 1) --------------------------

# The vehicle DP's stylised "AI" logotype is mis-read as "Al"/"GenAl"/"Fls" by
# the extractor. A doc flagged `normalise_glyphs: True` has these repaired before
# segmentation; an unflagged doc must be left untouched (DP-specific rule).
AI_DP_GLYPH_MARKDOWN = (
    "AI Discussion Paper\n\n"
    "3 Fair usage and bias\n\n"
    "3.5 A major challenge of Al revolves around GenAl models used by "
    "leading Fls.\n"
)
OUTSOURCING_AL_MARKDOWN = (
    "Outsourcing\n\n"
    "12 Approval for material outsourcing arrangements\n\n"
    "12.1 The service provider must not deploy Al without the Bank's "
    "written approval.\n"
)

NORMALISE_FIXTURE_DOCUMENTS = {
    "ai-dp-2025": {
        "policy_id": "ai-dp",
        "document_id": "ai-dp-2025",
        "title": "AI Discussion Paper",
        "version": "DP · 2025",
        "source_path": "ai-dp.pdf",
        "source": "published",
        "cluster": "ai-financial-sector",
        "normalise_glyphs": True,
    },
    "outsourcing-v1-2019": {
        "policy_id": "outsourcing",
        "document_id": "outsourcing-v1-2019",
        "title": "Outsourcing",
        "version": "v1 · 2019",
        "source_path": "outsourcing.pdf",
        "source": "published",
        "cluster": "technology-risk",
    },
}


def test_run_build_applies_glyph_normalisation_only_to_flagged_documents(tmp_path):
    """`normalise_glyphs: True` repairs the AI-glyph mis-reads on the vehicle
    document before segmentation, so its clause text is verbatim-correct; an
    unflagged document is left byte-for-byte (the bare Al→AI rule is DP-only)."""
    output_dir = tmp_path / "artifacts"
    markdown_by_path = {
        "ai-dp.pdf": AI_DP_GLYPH_MARKDOWN,
        "outsourcing.pdf": OUTSOURCING_AL_MARKDOWN,
    }

    run_build(
        documents=NORMALISE_FIXTURE_DOCUMENTS,
        curated_edges=[],
        draft_registry={"live_drafts": []},
        output_dir=output_dir,
        ingest_fn=lambda p: markdown_by_path[str(p)],
    )

    clause_index = json.loads(
        (output_dir / "clause-index.json").read_text(encoding="utf-8")
    )

    # Flagged vehicle document → glyphs repaired, keyed "AI-DP {number}".
    dp = clause_index["AI-DP 3.5"]["text"]
    assert "A major challenge of AI revolves" in dp
    assert "GenAI models" in dp
    assert "leading FIs" in dp
    assert "GenAl" not in dp and "Fls" not in dp
    assert not re.search(r"(?<![A-Za-z])Al(?![A-Za-z])", dp)

    # Unflagged document → NOT normalised; the bare "Al" survives untouched.
    outsourcing = clause_index["Outsourcing 12.1"]["text"]
    assert "deploy Al without" in outsourcing


def test_run_build_supports_multi_passage_reference(tmp_path):
    """A reference with a `passages` list contributes one verbatim clause per
    passage under a single graph node (e.g. BCBS 239 cited at both P3 and P4)."""
    output_dir = tmp_path / "artifacts"
    multi_passage_reference = {
        "bcbs-239": {
            "policy_id": "bcbs-239",
            "document_id": "bcbs-239",
            "title": "BCBS 239 — Principles for effective risk data aggregation",
            "version": "2013",
            "cluster": "ai-financial-sector",
            "kind": "reference",
            "source_type": "international_standard",
            "access": "public",
            "preview": False,
            "passages": [
                {
                    "anchor": "P4",
                    "heading": "Principle 4 — Completeness",
                    "passage": "Completeness passage four.",
                },
                {
                    "anchor": "P3",
                    "heading": "Principle 3 — Accuracy and Integrity",
                    "passage": "Accuracy passage three.",
                },
            ],
        },
    }

    run_build(
        documents=FIXTURE_DOCUMENTS,
        curated_edges=FIXTURE_CURATED_EDGES,
        draft_registry={"live_drafts": ["opres"]},
        output_dir=output_dir,
        ingest_fn=_stub_ingest_fn,
        reference_documents=multi_passage_reference,
        reference_edges=[],
    )

    clause_index = json.loads(
        (output_dir / "clause-index.json").read_text(encoding="utf-8")
    )
    # Both passages enter the index verbatim, under one document_id.
    assert clause_index["BCBS 239 P4"]["text"] == "Completeness passage four."
    assert clause_index["BCBS 239 P3"]["text"] == "Accuracy passage three."
    assert clause_index["BCBS 239 P4"]["document_id"] == "bcbs-239"
    assert clause_index["BCBS 239 P3"]["source"] == "reference"

    # One graph node, carrying the widened source_type vocabulary.
    graph = json.loads((output_dir / "graph.json").read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in graph["nodes"]}
    assert nodes["bcbs-239"]["source_type"] == "international_standard"


def test_run_build_emits_industry_feedback_passage_and_stance(tmp_path):
    """An industry_feedback source contributes its passage to the clause index and
    a graph node carrying its stance."""
    output_dir = tmp_path / "artifacts"
    feedback_reference = {
        "industry-fsp-3": {
            "policy_id": "industry-fsp-3",
            "document_id": "industry-fsp-3",
            "title": "Industry feedback — 3 FSP respondents",
            "version": "consultation response",
            "cluster": "ai-financial-sector",
            "kind": "reference",
            "source_type": "industry_feedback",
            "access": "public",
            "preview": False,
            "stance": "partial",
            "anchor": "FSP-3",
            "heading": "FSP respondents — data & personal information",
            "passage": "Informed consent is unworkable for legacy training datasets.",
        },
    }

    run_build(
        documents=FIXTURE_DOCUMENTS,
        curated_edges=FIXTURE_CURATED_EDGES,
        draft_registry={"live_drafts": ["opres"]},
        output_dir=output_dir,
        ingest_fn=_stub_ingest_fn,
        reference_documents=feedback_reference,
        reference_edges=[],
    )

    clause_index = json.loads(
        (output_dir / "clause-index.json").read_text(encoding="utf-8")
    )
    assert clause_index["Industry FSP-3"]["text"] == (
        "Informed consent is unworkable for legacy training datasets."
    )

    graph = json.loads((output_dir / "graph.json").read_text(encoding="utf-8"))
    node = {n["id"]: n for n in graph["nodes"]}["industry-fsp-3"]
    assert node["source_type"] == "industry_feedback"
    assert node["stance"] == "partial"


def test_build_dispatches_by_doc_class(tmp_path):
    documents = {
        "rmit-v2-2025": {"document_id": "rmit-v2-2025", "policy_id": "rmit",
                         "segmenter_class": "structured-rules", "source_path": "x.pdf"},
        "eu-ai-act": {"document_id": "eu-ai-act", "policy_id": "eu-ai-act",
                      "segmenter_class": "legislative", "source_path": "y.pdf",
                      "shortname": "EU AI Act"},
    }
    md = {
        "rmit-v2-2025": "10.1 A financial institution must establish a framework.\n",
        "eu-ai-act": "Article 1\n\nThis Regulation lays down rules.\n",
    }

    def ingest(path):
        return md["rmit-v2-2025"] if str(path) == "x.pdf" else md["eu-ai-act"]

    def boundary(document_id, source_markdown, doc_class):
        return [{"anchor_label": "Article 1",
                 "starts_with": "This Regulation lays down rules",
                 "parent": None}]

    index = build_anchor_index(
        documents, ingest_fn=ingest, boundary_fn=boundary, output_dir=tmp_path)
    ids = {a["anchor_id"] for a in index.all()}
    assert "RMiT 10.1" in ids            # BNM lane
    assert "EU AI Act Article 1" in ids  # LLM lane
    written = json.loads((tmp_path / "anchor-index.json").read_text("utf-8"))
    assert len(written) == len(index)


# --- Completeness guard (Problem B: nondeterministic boundary-model runs) ---

# Five distinct, unambiguous, `starts_with`-locatable article bodies — enough
# that a stub boundary_fn can be made to "find" all five (passing case) or
# only two of them (truncated-run case).
COMPLETENESS_MARKDOWN = (
    "Some Act\n\n"
    "Article 1\n\nThis Regulation lays down rules on one subject matter.\n\n"
    "Article 2\n\nThis Regulation lays down rules on a second subject matter.\n\n"
    "Article 3\n\nThis Regulation lays down rules on a third subject matter.\n\n"
    "Article 4\n\nThis Regulation lays down rules on a fourth subject matter.\n\n"
    "Article 5\n\nThis Regulation lays down rules on a fifth subject matter.\n"
)

_ALL_FIVE_UNITS = [
    {"anchor_label": "Article 1",
     "starts_with": "This Regulation lays down rules on one subject matter",
     "parent": None},
    {"anchor_label": "Article 2",
     "starts_with": "This Regulation lays down rules on a second subject matter",
     "parent": None},
    {"anchor_label": "Article 3",
     "starts_with": "This Regulation lays down rules on a third subject matter",
     "parent": None},
    {"anchor_label": "Article 4",
     "starts_with": "This Regulation lays down rules on a fourth subject matter",
     "parent": None},
    {"anchor_label": "Article 5",
     "starts_with": "This Regulation lays down rules on a fifth subject matter",
     "parent": None},
]


def test_build_anchor_index_raises_on_implausibly_low_anchor_count(tmp_path):
    """A doc declaring `min_anchors` whose boundary_fn returns too few resolvable
    units (simulating a truncated boundary-model run) must raise
    AnchorCompletenessError, and NOTHING is written to output_dir — the raise
    happens before the write, so a truncated run can never silently commit a
    broken anchor-index.json."""
    documents = {
        "some-act": {
            "document_id": "some-act",
            "policy_id": "some-act",
            "segmenter_class": "legislative",
            "source_path": "some-act.pdf",
            "shortname": "Some Act",
            "min_anchors": 5,
        },
    }

    def ingest(path):
        return COMPLETENESS_MARKDOWN

    def boundary(document_id, source_markdown, doc_class):
        # Truncated run: only the first two units come back.
        return _ALL_FIVE_UNITS[:2]

    with pytest.raises(AnchorCompletenessError):
        build_anchor_index(
            documents, ingest_fn=ingest, boundary_fn=boundary, output_dir=tmp_path
        )

    assert not (tmp_path / "anchor-index.json").exists()


def test_build_anchor_index_without_min_anchors_is_unguarded(tmp_path):
    """A document with no `min_anchors` floor builds normally regardless of how
    few anchors the segmenter produces (backward compatible: structured-rules/
    BNM docs declare no floor)."""
    documents = {
        "some-act": {
            "document_id": "some-act",
            "policy_id": "some-act",
            "segmenter_class": "legislative",
            "source_path": "some-act.pdf",
            "shortname": "Some Act",
            # No min_anchors key at all.
        },
    }

    def ingest(path):
        return COMPLETENESS_MARKDOWN

    def boundary(document_id, source_markdown, doc_class):
        return _ALL_FIVE_UNITS[:2]

    index = build_anchor_index(
        documents, ingest_fn=ingest, boundary_fn=boundary, output_dir=tmp_path
    )

    assert len(index) == 2
    written = json.loads((tmp_path / "anchor-index.json").read_text("utf-8"))
    assert len(written) == 2


def test_build_anchor_index_min_anchors_met_builds_normally(tmp_path):
    """A document whose `min_anchors` floor IS met builds and writes the
    artifact exactly as an unguarded document would (existing behavior
    unchanged when the guard doesn't fire)."""
    documents = {
        "some-act": {
            "document_id": "some-act",
            "policy_id": "some-act",
            "segmenter_class": "legislative",
            "source_path": "some-act.pdf",
            "shortname": "Some Act",
            "min_anchors": 5,
        },
    }

    def ingest(path):
        return COMPLETENESS_MARKDOWN

    def boundary(document_id, source_markdown, doc_class):
        return _ALL_FIVE_UNITS

    index = build_anchor_index(
        documents, ingest_fn=ingest, boundary_fn=boundary, output_dir=tmp_path
    )

    assert len(index) == 5
    written = json.loads((tmp_path / "anchor-index.json").read_text("utf-8"))
    assert len(written) == 5
