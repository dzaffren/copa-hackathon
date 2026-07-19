"""Tests for engine.build.build_anchor_index — Task 7 of
`docs/specs/workstream-brain/spec-engine-anchor-segmentation.md`.

The build pipeline reads `data/corpus/manifest.json`, dispatches each
`in_mvp1: true` document through the doc_class-appropriate segmenter, unions
the anchors into one `AnchorIndex`, and writes
`data/artifacts/anchor-index.json` as a list of `Anchor` dicts.

No network access. Tests exercise `build_anchor_index` with hand-crafted
manifests + a stubbed ingest function so no PDFs are touched. The verbatim
guardrail (every anchor.text a literal substring of the source markdown) is
checked in a dedicated test.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from engine.anchors import Anchor, AnchorIndex
from engine.build import build_anchor_index

# Minimal hand-crafted markdown per doc_class, verified end-to-end below.

_STRUCTURED_RULES_MARKDOWN = (
    "Outsourcing\n\n"
    "12 Approval for material outsourcing arrangements\n\n"
    "12.1 A financial institution must obtain the Bank's written approval "
    "before entering into a new material outsourcing arrangement.\n"
)

_SEMI_STRUCTURED_MARKDOWN = (
    "# Section 7 Credit Risk\n\n"
    "## 7.3 Standardised Approach\n\n"
    "### 7.3.15 Risk weights\n\n"
    "A bank shall apply the risk weights set out in the table below to its "
    "credit exposures under the standardised approach.\n"
)

_PROSE_MARKDOWN = (
    "# Chapter 3\n\n" + ("A bank must monitor its operational resilience. " * 20) + "\n"
)


def _write_manifest(tmp_path: Path, documents: list[dict]) -> Path:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps({"documents": documents}, indent=2), encoding="utf-8"
    )
    return manifest_path


def _make_ingest_stub(markdown_by_path: dict[str, str]):
    """Key on the file basename — the build resolves paths against repo_root,
    so the ingest_fn receives the full absolute path, not the manifest's
    relative source_path.
    """

    def _stub(path):
        return markdown_by_path[Path(path).name]

    return _stub


def _touch_manifest_sources(tmp_path: Path, documents: list[dict]) -> None:
    """Create empty stand-in files at every entry's `source_path` so the
    build's `require_source_exists` check passes for tests that use a
    stubbed `ingest_fn`.
    """
    for entry in documents:
        source = tmp_path / entry["source_path"]
        source.parent.mkdir(parents=True, exist_ok=True)
        source.touch()


def test_build_anchor_index_from_minimal_manifest(tmp_path):
    """Given one document per doc_class, the build unions their anchors into
    a single AnchorIndex spanning all three strategies."""
    documents = [
        {
            "document_id": "outsourcing",  # POLICY_SHORT_NAMES key
            "title": "Outsourcing PD",
            "jurisdiction": "MY",
            "issuer": "BNM",
            "doc_class": "structured-rules",
            "source_path": "outsourcing.pdf",
            "in_mvp1": True,
        },
        {
            "document_id": "mas-637",
            "title": "MAS Notice 637",
            "jurisdiction": "SG",
            "issuer": "MAS",
            "doc_class": "semi-structured",
            "source_path": "mas-637.pdf",
            "in_mvp1": True,
            "shortname": "MAS 637",
        },
        {
            "document_id": "boe-ch3",
            "title": "BoE Chapter 3",
            "jurisdiction": "UK",
            "issuer": "Bank of England",
            "doc_class": "prose",
            "source_path": "boe-ch3.pdf",
            "in_mvp1": True,
            "shortname": "BoE Ch3",
        },
    ]
    manifest_path = _write_manifest(tmp_path, documents)
    ingest_stub = _make_ingest_stub(
        {
            "outsourcing.pdf": _STRUCTURED_RULES_MARKDOWN,
            "mas-637.pdf": _SEMI_STRUCTURED_MARKDOWN,
            "boe-ch3.pdf": _PROSE_MARKDOWN,
        }
    )

    index = build_anchor_index(
        manifest_path=manifest_path,
        artifacts_dir=tmp_path / "artifacts",
        ingest_fn=ingest_stub,
        repo_root=tmp_path,
        require_source_exists=False,
    )

    doc_classes = {a["doc_class"] for a in index.all()}
    assert doc_classes == {"structured-rules", "semi-structured", "prose"}
    assert len(index) >= 3


def test_build_anchor_index_skips_missing_source_path(tmp_path, caplog):
    """A manifest entry whose source_path does not exist on disk is logged
    and skipped — the build must not crash on it."""
    documents = [
        {
            "document_id": "outsourcing",
            "title": "Outsourcing PD",
            "jurisdiction": "MY",
            "issuer": "BNM",
            "doc_class": "structured-rules",
            "source_path": "outsourcing.pdf",
            "in_mvp1": True,
        },
        {
            "document_id": "vanished-doc",
            "title": "Not on disk",
            "jurisdiction": "MY",
            "issuer": "BNM",
            "doc_class": "structured-rules",
            "source_path": "does/not/exist.pdf",
            "in_mvp1": True,
        },
    ]
    manifest_path = _write_manifest(tmp_path, documents)
    # Touch only the outsourcing.pdf; leave "does/not/exist.pdf" absent.
    (tmp_path / "outsourcing.pdf").touch()
    ingest_stub = _make_ingest_stub({"outsourcing.pdf": _STRUCTURED_RULES_MARKDOWN})

    with caplog.at_level(logging.WARNING):
        index = build_anchor_index(
            manifest_path=manifest_path,
            artifacts_dir=tmp_path / "artifacts",
            ingest_fn=ingest_stub,
            repo_root=tmp_path,
            require_source_exists=True,
        )

    # Vanished doc did not contribute anchors.
    assert not index.by_document("vanished-doc")
    assert index.by_document("outsourcing")
    # A warning was logged naming the missing document.
    assert any("vanished-doc" in rec.message for rec in caplog.records)


def test_build_anchor_index_writes_json_reloadable(tmp_path):
    """The written anchor-index.json is a list of Anchor dicts that round-trips
    through `AnchorIndex(loaded)` — `.get(known_anchor_id)` returns the anchor.
    """
    documents = [
        {
            "document_id": "outsourcing",
            "title": "Outsourcing PD",
            "jurisdiction": "MY",
            "issuer": "BNM",
            "doc_class": "structured-rules",
            "source_path": "outsourcing.pdf",
            "in_mvp1": True,
        },
    ]
    manifest_path = _write_manifest(tmp_path, documents)
    _touch_manifest_sources(tmp_path, documents)
    ingest_stub = _make_ingest_stub({"outsourcing.pdf": _STRUCTURED_RULES_MARKDOWN})
    artifacts_dir = tmp_path / "artifacts"

    build_anchor_index(
        manifest_path=manifest_path,
        artifacts_dir=artifacts_dir,
        ingest_fn=ingest_stub,
        repo_root=tmp_path,
    )

    out_path = artifacts_dir / "anchor-index.json"
    assert out_path.exists()
    loaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert isinstance(loaded, list)
    reloaded = AnchorIndex(loaded)
    assert reloaded.get("Outsourcing 12.1") is not None
    assert (
        "written approval"
        in reloaded.get("Outsourcing 12.1")["text"]  # type: ignore[index]
    )


def test_build_anchor_index_substring_verification(tmp_path):
    """If a segmenter emits an anchor whose text is not a literal substring of
    the source markdown, `build_anchor_index` raises loudly — the verbatim
    guardrail must never silently pass."""
    documents = [
        {
            "document_id": "hand-crafted",
            "title": "Hand-crafted",
            "jurisdiction": "MY",
            "issuer": "BNM",
            "doc_class": "prose",
            "source_path": "hand-crafted.pdf",
            "in_mvp1": True,
            "shortname": "HC",
        },
    ]
    manifest_path = _write_manifest(tmp_path, documents)
    _touch_manifest_sources(tmp_path, documents)

    # A stub segmenter that emits an anchor whose text is NOT in the source.
    def _bad_segmenter(document_id: str, source_markdown: str) -> list[Anchor]:
        return [
            {
                "anchor_id": "HC bad",
                "anchor_label": "HC bad",
                "text": "THIS TEXT IS NOT IN THE SOURCE MARKDOWN",
                "doc_class": "prose",
                "document_id": document_id,
                "heading_path": [],
                "page_span": None,
                "parent_anchor": None,
            }
        ]

    ingest_stub = _make_ingest_stub({"hand-crafted.pdf": _PROSE_MARKDOWN})

    from engine.anchors import AnchorTextNotFoundError, SegmenterRegistry

    bad_registry = SegmenterRegistry()
    bad_registry.register("prose", _bad_segmenter)

    with pytest.raises(AnchorTextNotFoundError):
        build_anchor_index(
            manifest_path=manifest_path,
            artifacts_dir=tmp_path / "artifacts",
            ingest_fn=ingest_stub,
            repo_root=tmp_path,
            segmenter_registry=bad_registry,
        )


def test_build_anchor_index_excludes_in_mvp1_false(tmp_path):
    """Documents with `in_mvp1: false` are excluded from the build even if
    their source file exists and the segmenter would succeed."""
    documents = [
        {
            "document_id": "outsourcing",
            "title": "Outsourcing PD",
            "jurisdiction": "MY",
            "issuer": "BNM",
            "doc_class": "structured-rules",
            "source_path": "outsourcing.pdf",
            "in_mvp1": True,
        },
        {
            "document_id": "archived-outsourcing",
            "title": "Archived Outsourcing PD",
            "jurisdiction": "MY",
            "issuer": "BNM",
            "doc_class": "structured-rules",
            "source_path": "archived.pdf",
            "in_mvp1": False,
        },
    ]
    manifest_path = _write_manifest(tmp_path, documents)
    _touch_manifest_sources(tmp_path, documents)
    ingest_stub = _make_ingest_stub(
        {
            "outsourcing.pdf": _STRUCTURED_RULES_MARKDOWN,
            "archived.pdf": _STRUCTURED_RULES_MARKDOWN,
        }
    )

    index = build_anchor_index(
        manifest_path=manifest_path,
        artifacts_dir=tmp_path / "artifacts",
        ingest_fn=ingest_stub,
        repo_root=tmp_path,
    )

    assert index.by_document("outsourcing")
    assert not index.by_document("archived-outsourcing")
