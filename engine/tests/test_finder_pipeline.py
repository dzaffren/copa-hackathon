"""Tests for the finder pipeline (engine/finder_pipeline.py).

Covers the spec's Test Scenarios 1-9
(docs/specs/workstream-brain/spec-engine-arm-g-pipeline.md). No live model
calls — every stage's ``call_chat`` is monkeypatched, mirroring how the existing
engine tests stub the network seam. Deployment routing is asserted by capturing
the ``deployment`` argument each ``call_chat`` receives.
"""

import json

import pytest

from engine.anchors import Anchor, AnchorIndex


def _anchor(anchor_id: str, document_id: str, text: str) -> Anchor:
    return {
        "anchor_id": anchor_id,
        "anchor_label": anchor_id,
        "text": text,
        "doc_class": "structured-rules",
        "document_id": document_id,
        "heading_path": [],
        "page_span": None,
        "parent_anchor": None,
    }


# ---------------------------------------------------------------------------
# Test 8 — cache invalidation on cap change.
# ---------------------------------------------------------------------------


def test_axis_cache_invalidated_on_cap_change(tmp_path, monkeypatch):
    """A cache entry written with axis_cap=5 whose anchor text now yields a
    different cap is a MISS → re-extraction → the entry is rewritten with the
    new cap."""
    import engine.finder_pipeline as finder_pipeline

    monkeypatch.setattr(finder_pipeline, "AXES_DIR", tmp_path)

    # A long anchor: cap = min(12, max(5, ceil(len/400))). ~2400 chars → cap 6.
    long_text = "x" * 2400
    index = AnchorIndex([_anchor("DOC 1.1", "doc-a", long_text)])

    # Seed a stale cache entry with axis_cap=5 (wrong for this text).
    stale = {
        "document_id": "doc-a",
        "model": "old-model",
        "anchors": [
            {
                "anchor_id": "DOC 1.1",
                "text_hash": finder_pipeline._text_hash(long_text),
                "axis_cap": 5,
                "axes": ["stale axis"],
            }
        ],
    }
    (tmp_path / "axes-doc-a.json").write_text(json.dumps(stale), encoding="utf-8")

    calls = []

    def fake_call_chat(deployment, system, user, max_tokens=None):
        calls.append(deployment)
        return json.dumps(["fresh axis one", "fresh axis two"])

    monkeypatch.setattr(finder_pipeline, "call_chat", fake_call_chat)

    result = finder_pipeline.extract_axes_for_document(index, "doc-a")

    # Cap change forced a re-extraction (one model call).
    assert len(calls) == 1
    assert result["DOC 1.1"] == ["fresh axis one", "fresh axis two"]

    # The entry is rewritten with the correct new cap.
    rewritten = json.loads((tmp_path / "axes-doc-a.json").read_text(encoding="utf-8"))
    entry = rewritten["anchors"][0]
    assert entry["axis_cap"] == finder_pipeline._axis_cap(long_text)
    assert entry["axis_cap"] != 5
    assert entry["axes"] == ["fresh axis one", "fresh axis two"]


def test_axis_cache_hit_skips_extraction(tmp_path, monkeypatch):
    """When text_hash AND axis_cap both match, the entry is reused with no model
    call."""
    import engine.finder_pipeline as finder_pipeline

    monkeypatch.setattr(finder_pipeline, "AXES_DIR", tmp_path)

    text = "A short clause about consent."
    index = AnchorIndex([_anchor("DOC 1.1", "doc-a", text)])

    fresh = {
        "document_id": "doc-a",
        "model": "m",
        "anchors": [
            {
                "anchor_id": "DOC 1.1",
                "text_hash": finder_pipeline._text_hash(text),
                "axis_cap": finder_pipeline._axis_cap(text),
                "axes": ["cached axis"],
            }
        ],
    }
    (tmp_path / "axes-doc-a.json").write_text(json.dumps(fresh), encoding="utf-8")

    def boom(*a, **k):  # pragma: no cover - must not be called
        raise AssertionError("call_chat should not run on a cache hit")

    monkeypatch.setattr(finder_pipeline, "call_chat", boom)

    result = finder_pipeline.extract_axes_for_document(index, "doc-a")
    assert result["DOC 1.1"] == ["cached axis"]


def test_axis_cap_scales_with_length():
    """A long dense anchor gets a higher cap than a short one, both bounded."""
    import engine.finder_pipeline as finder_pipeline

    short = finder_pipeline._axis_cap("A single short sentence.")
    long = finder_pipeline._axis_cap("x" * 4000)
    assert short == 5
    assert long > short
    assert long <= 12


# ---------------------------------------------------------------------------
# Stage 3 fixtures — a small A/B corpus and a 16-pair candidate list (2 batches).
# ---------------------------------------------------------------------------


def _stage3_index() -> AnchorIndex:
    anchors = [_anchor(f"ED {i}", "doc-a", f"ED clause {i}") for i in range(1, 9)]
    anchors += [_anchor(f"HKMA {i}", "doc-b", f"HKMA clause {i}") for i in range(1, 9)]
    return AnchorIndex(anchors)


def _stage3_candidates() -> list[dict]:
    return [
        {
            "source_anchor_id": f"ED {i}",
            "target_anchor_id": f"HKMA {i}",
            "matched_axis_source": f"axis-{i}",
            "matched_axis_target": f"axis-{i}",
            "similarity": 0.7,
            "signal": "cosine",
        }
        for i in range(1, 17)  # 16 pairs — but only ED/HKMA 1..8 exist
    ]


# ---------------------------------------------------------------------------
# Test 2 — batch-union membership: a cross-pair A×B, both in the batch, accepted.
# ---------------------------------------------------------------------------


def test_batch_union_membership_accepts_cross_pair(monkeypatch):
    """Retrieval paired ED 1×HKMA 1 and ED 2×HKMA 2; the finder cites the
    cross-pair ED 1×HKMA 2. Both anchors are in the batch union, so the finding
    is returned; source ids are only A-side, target ids only B-side."""
    import engine.finder_pipeline as finder_pipeline

    anchors = [
        _anchor("ED 1", "doc-a", "ED one"),
        _anchor("ED 2", "doc-a", "ED two"),
        _anchor("HKMA 1", "doc-b", "HKMA one"),
        _anchor("HKMA 2", "doc-b", "HKMA two"),
    ]
    index = AnchorIndex(anchors)
    candidates = [
        {"source_anchor_id": "ED 1", "target_anchor_id": "HKMA 1"},
        {"source_anchor_id": "ED 2", "target_anchor_id": "HKMA 2"},
    ]

    captured_users = []

    def fake_call_chat(deployment, system, user, max_tokens=None):
        captured_users.append(user)
        return json.dumps(
            [
                {
                    "summary": "cross-pair relation",
                    "label": "differs-on",
                    "sentiment": "tighten",
                    "source_clauses": ["ED 1"],
                    "target_clauses": ["HKMA 2"],
                }
            ]
        )

    monkeypatch.setattr(finder_pipeline, "call_chat", fake_call_chat)

    findings = finder_pipeline.finder_same_topic_batched(index, candidates)

    assert len(findings) == 1
    finding = findings[0]
    assert finding["source_clauses"] == ["ED 1"]
    assert finding["target_clauses"] == ["HKMA 2"]
    # Both sides of the batch union were shown to the finder.
    assert "ED 1" in captured_users[0] and "ED 2" in captured_users[0]
    assert "HKMA 1" in captured_users[0] and "HKMA 2" in captured_users[0]


def test_batch_partitions_anchors_by_side(monkeypatch):
    """The A-side list and B-side list are presented separately in the prompt."""
    import engine.finder_pipeline as finder_pipeline

    index = _stage3_index()
    candidates = _stage3_candidates()[:8]  # ED/HKMA 1..8

    captured = []

    def fake_call_chat(deployment, system, user, max_tokens=None):
        captured.append(user)
        return "[]"

    monkeypatch.setattr(finder_pipeline, "call_chat", fake_call_chat)
    finder_pipeline.finder_same_topic_batched(index, candidates)

    user = captured[0]
    a_pos = user.index("A-side anchors")
    b_pos = user.index("B-side anchors")
    assert a_pos < b_pos
    # ED ids appear in the A-side region, HKMA ids in the B-side region.
    assert "ED 1" in user[a_pos:b_pos]
    assert "HKMA 1" in user[b_pos:]


# ---------------------------------------------------------------------------
# Test 3 — batch failure: retry once (succeed), and skip-after-second-failure.
# ---------------------------------------------------------------------------


def test_batch_failure_retries_once_then_succeeds(monkeypatch):
    """A batch whose first call raises but whose retry succeeds is retried
    exactly once and its findings kept."""
    import engine.finder_pipeline as finder_pipeline

    index = _stage3_index()
    candidates = _stage3_candidates()[:8]

    calls = {"n": 0}

    def flaky_call_chat(deployment, system, user, max_tokens=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise finder_pipeline.LLMResponseError("boom on first try")
        return json.dumps(
            [
                {
                    "summary": "ok",
                    "label": "aligns-with",
                    "source_clauses": ["ED 1"],
                    "target_clauses": ["HKMA 1"],
                }
            ]
        )

    monkeypatch.setattr(finder_pipeline, "call_chat", flaky_call_chat)

    findings = finder_pipeline.finder_same_topic_batched(index, candidates)
    assert calls["n"] == 2  # one failure + one retry
    assert len(findings) == 1


def test_batch_failure_skips_and_logs_pair_ids(monkeypatch, caplog):
    """A batch that fails on both attempts is skipped, every pair id is logged,
    and the pipeline continues (returns findings from other batches)."""
    import logging

    import engine.finder_pipeline as finder_pipeline

    index = _stage3_index()
    # 8 candidates → a single batch, which always fails on both attempts.
    candidates = _stage3_candidates()[:8]

    def always_fails(deployment, system, user, max_tokens=None):
        raise finder_pipeline.LLMResponseError("always fails")

    monkeypatch.setattr(finder_pipeline, "call_chat", always_fails)

    with caplog.at_level(logging.WARNING):
        findings = finder_pipeline.finder_same_topic_batched(index, candidates)

    assert findings == []  # the only batch was skipped
    # Every dropped pair id from the batch is logged.
    logged = "\n".join(r.message for r in caplog.records)
    assert "skipped after retry" in logged
    assert "ED 1 × HKMA 1" in logged
    assert "ED 8 × HKMA 8" in logged


# ---------------------------------------------------------------------------
# Stage 4 — suppression build.
# ---------------------------------------------------------------------------

_SUPP_CANDIDATES = [
    {
        "source_anchor_id": "A1",
        "target_anchor_id": "B1",
        "matched_axis_source": "consent-management",
        "matched_axis_target": "user-consent",
    },
    {
        "source_anchor_id": "A2",
        "target_anchor_id": "B2",
        "matched_axis_source": "authentication",
        "matched_axis_target": "identity-verification",
    },
]


def test_build_suppression_covers_only_matched_source():
    """Only candidates whose A-side anchor produced a finding contribute; the
    A1 finding covers the A1×B1 pair and its axes, not the A2 pair."""
    import engine.finder_pipeline as finder_pipeline

    findings = [
        {
            "summary": "Both require consent",
            "label": "aligns-with",
            "source_clauses": ["A1"],
            "target_clauses": ["B1"],
        }
    ]
    result = finder_pipeline._build_suppression(_SUPP_CANDIDATES, findings)
    assert "A1 × B1" in result["covered_pairs"]
    assert "A2 × B2" not in result["covered_pairs"]
    assert "consent-management" in result["covered_topics"]
    assert "user-consent" in result["covered_topics"]
    assert "authentication" not in result["covered_topics"]
    # Sorted + de-duplicated.
    assert result["covered_topics"] == sorted(set(result["covered_topics"]))


def test_build_suppression_empty_findings():
    import engine.finder_pipeline as finder_pipeline

    result = finder_pipeline._build_suppression(_SUPP_CANDIDATES, [])
    assert result == {"covered_pairs": [], "covered_topics": []}


# ---------------------------------------------------------------------------
# Stage 5 — whole-doc coverage finder.
# ---------------------------------------------------------------------------


def _coverage_index() -> AnchorIndex:
    return AnchorIndex(
        [
            _anchor("A1", "doc-a", "A requires explicit consent."),
            _anchor("B1", "doc-b", "B requires user consent."),
        ]
    )


def test_coverage_finder_uses_coverage_prompt_and_finder_critic(monkeypatch):
    """Stage 5 calls call_chat with COVERAGE_FINDER_SYSTEM_PROMPT and the
    FINDER_CRITIC_DEPLOYMENT (large) tier."""
    import engine.finder_pipeline as finder_pipeline

    captured = {}

    def fake_call_chat(deployment, system, user, max_tokens=None):
        captured["deployment"] = deployment
        captured["system"] = system
        captured["user"] = user
        return "[]"

    monkeypatch.setattr(finder_pipeline, "call_chat", fake_call_chat)
    finder_pipeline.finder_coverage_whole_doc(
        _coverage_index(), "doc-a", "doc-b", {"covered_topics": [], "covered_pairs": []}
    )

    assert captured["system"] == finder_pipeline.COVERAGE_FINDER_SYSTEM_PROMPT
    assert captured["deployment"] == finder_pipeline.FINDER_CRITIC_DEPLOYMENT
    assert "A requires explicit consent" in captured["user"]
    assert "B requires user consent" in captured["user"]


def test_coverage_finder_appends_suppression_block_when_topics_present(monkeypatch):
    import engine.finder_pipeline as finder_pipeline

    captured = {}

    def fake_call_chat(deployment, system, user, max_tokens=None):
        captured["user"] = user
        return "[]"

    monkeypatch.setattr(finder_pipeline, "call_chat", fake_call_chat)
    finder_pipeline.finder_coverage_whole_doc(
        _coverage_index(),
        "doc-a",
        "doc-b",
        {"covered_topics": ["consent-management"], "covered_pairs": ["A1 × B1"]},
    )
    assert "TOPICS ALREADY COVERED" in captured["user"]
    assert "consent-management" in captured["user"]


def test_coverage_finder_no_suppression_block_when_empty(monkeypatch):
    import engine.finder_pipeline as finder_pipeline

    captured = {}

    def fake_call_chat(deployment, system, user, max_tokens=None):
        captured["user"] = user
        return "[]"

    monkeypatch.setattr(finder_pipeline, "call_chat", fake_call_chat)
    finder_pipeline.finder_coverage_whole_doc(
        _coverage_index(), "doc-a", "doc-b", {"covered_topics": [], "covered_pairs": []}
    )
    assert "TOPICS ALREADY COVERED" not in captured["user"]


def test_is_single_sided():
    import engine.finder_pipeline as finder_pipeline

    assert finder_pipeline._is_single_sided(
        {"label": "goes-beyond", "source_clauses": ["A1"], "target_clauses": []}
    )
    assert finder_pipeline._is_single_sided(
        {"label": "silent-on", "source_clauses": [], "target_clauses": ["B1"]}
    )
    assert not finder_pipeline._is_single_sided(
        {"label": "goes-beyond", "source_clauses": ["A1"], "target_clauses": ["B1"]}
    )
    assert not finder_pipeline._is_single_sided(
        {"label": "aligns-with", "source_clauses": ["A1"], "target_clauses": ["B1"]}
    )


def test_is_redundant():
    import engine.finder_pipeline as finder_pipeline

    supp = {"covered_topics": ["consent management"], "covered_pairs": ["A1 × B1"]}
    assert finder_pipeline._is_redundant(
        {"summary": "gap on consent management cadence", "source_clauses": []}, supp
    )
    assert finder_pipeline._is_redundant(
        {"summary": "unrelated", "source_clauses": ["A1"], "target_clauses": []}, supp
    )
    assert not finder_pipeline._is_redundant(
        {"summary": "unrelated topic", "source_clauses": ["A9"], "target_clauses": []},
        supp,
    )


# ---------------------------------------------------------------------------
# Test 1 — same-topic labels restricted (batched): a stubbed silent-on from the
# same-topic stage is rejected; only aligns/differs/conflicts survive.
# ---------------------------------------------------------------------------


def test_same_topic_stage_rejects_coverage_labels(monkeypatch):
    import engine.finder_pipeline as finder_pipeline

    index = _stage3_index()
    candidates = _stage3_candidates()[:16]  # 2 batches of 8 (only 1..8 resolve)

    def fake_call_chat(deployment, system, user, max_tokens=None):
        return json.dumps(
            [
                {
                    "summary": "leaked coverage label",
                    "label": "silent-on",
                    "source_clauses": [],
                    "target_clauses": ["HKMA 1"],
                },
                {
                    "summary": "genuine same-topic",
                    "label": "aligns-with",
                    "source_clauses": ["ED 1"],
                    "target_clauses": ["HKMA 1"],
                },
            ]
        )

    monkeypatch.setattr(finder_pipeline, "call_chat", fake_call_chat)
    findings = finder_pipeline.finder_same_topic_batched(index, candidates)

    labels = {f["label"] for f in findings}
    assert "silent-on" not in labels
    assert labels <= set(finder_pipeline.SAME_TOPIC_LABELS)
    assert "aligns-with" in labels


# ---------------------------------------------------------------------------
# Stage 6 — reformatter recovers / refuses; single-sided validates.
# ---------------------------------------------------------------------------


def _rmit_index() -> AnchorIndex:
    return AnchorIndex(
        [
            _anchor("RMiT 2.1", "doc-a", "RMiT clause two point one."),
            _anchor("RMiT 2.2(b)", "doc-a", "RMiT clause two point two b."),
            _anchor("HKMA OpenAPI 17.2", "doc-b", "HKMA clause seventeen point two."),
        ]
    )


# Test 4 — reformatter recovers punctuation/prefix drift.


def test_reformatter_recovers_trailing_punct_and_bare_prefix():
    import engine.finder_pipeline as finder_pipeline

    index = _rmit_index()

    # "RMiT 2.2(b):" → strip trailing ":" → "RMiT 2.2(b)".
    assert finder_pipeline._reformat_citation("RMiT 2.2(b):", "doc-a", index) == (
        "RMiT 2.2(b)",
        "strip_trailing_punct",
    )
    # Bare "2.1" → restore prefix "RMiT" → "RMiT 2.1".
    assert finder_pipeline._reformat_citation("2.1", "doc-a", index) == (
        "RMiT 2.1",
        "restore_prefix",
    )


def test_stage6_records_rewrites_and_marks_supported():
    import engine.finder_pipeline as finder_pipeline

    index = _rmit_index()
    coverage = [
        {
            "summary": "gap",
            "label": "goes-beyond",
            "source_clauses": ["RMiT 2.2(b):", "2.1"],
            "target_clauses": [],
        }
    ]
    connections, unsupported, _validation, rewrites = finder_pipeline.merge_reformat_validate(
        [], coverage, index, "doc-a", "doc-b"
    )
    assert len(connections) == 1
    assert unsupported == []
    raws = {r["cited_raw"]: r for r in rewrites}
    assert raws["RMiT 2.2(b):"]["cited_normalized"] == "RMiT 2.2(b)"
    assert raws["RMiT 2.2(b):"]["transform"] == "strip_trailing_punct"
    assert raws["2.1"]["cited_normalized"] == "RMiT 2.1"
    assert raws["2.1"]["transform"] == "restore_prefix"


# Test 5 — reformatter refuses unsafe rescue.


def test_reformatter_refuses_unsafe_rescue():
    import engine.finder_pipeline as finder_pipeline

    index = _rmit_index()
    assert finder_pipeline._reformat_citation("B 7.", "doc-a", index) is None
    assert finder_pipeline._reformat_citation('"5. Conclusion" chunk#68', "doc-a", index) is None


def test_stage6_demotes_unresolvable_without_rewrite():
    import engine.finder_pipeline as finder_pipeline

    index = _rmit_index()
    coverage = [
        {
            "summary": "invented",
            "label": "silent-on",
            "source_clauses": [],
            "target_clauses": ["B 7."],
        }
    ]
    connections, unsupported, _v, rewrites = finder_pipeline.merge_reformat_validate(
        [], coverage, index, "doc-a", "doc-b"
    )
    assert connections == []
    assert len(unsupported) == 1
    assert "No matching clause found" in unsupported[0]["message"]
    assert rewrites == []


# Test 6 — single-sided coverage finding validates supported.


def test_single_sided_coverage_validates_supported():
    import engine.finder_pipeline as finder_pipeline

    index = _rmit_index()
    coverage = [
        {
            "summary": "silent on X",
            "label": "silent-on",
            "source_clauses": [],
            "target_clauses": ["HKMA OpenAPI 17.2"],
        }
    ]
    connections, unsupported, _v, _r = finder_pipeline.merge_reformat_validate(
        [], coverage, index, "doc-a", "doc-b"
    )
    assert len(connections) == 1
    assert unsupported == []


# ---------------------------------------------------------------------------
# Orchestration — Tests 7 and 9.
# ---------------------------------------------------------------------------


def _orchestration_index() -> AnchorIndex:
    return AnchorIndex(
        [
            _anchor("ED 1", "doc-a", "ED requires consent revocation cadence."),
            _anchor("ED 2", "doc-a", "ED requires strong authentication."),
            _anchor("HKMA 1", "doc-b", "HKMA addresses consent."),
            _anchor("HKMA 2", "doc-b", "HKMA addresses authentication."),
        ]
    )


def _install_orchestration_stubs(monkeypatch, tmp_path, deployments):
    """Stub axis extraction (bypass model), retrieval, and call_chat routing.

    Records the deployment each stage's call_chat uses into ``deployments``.
    """
    import engine.finder_pipeline as finder_pipeline

    monkeypatch.setattr(finder_pipeline, "AXES_DIR", tmp_path)

    def fake_extract(
        anchor_index,
        document_id,
        deployment=finder_pipeline.EXTRACTION_DEPLOYMENT,
        axes_dir=None,
    ):
        deployments.append(("extract", deployment))
        return {a["anchor_id"]: ["axis"] for a in anchor_index.by_document(document_id)}

    monkeypatch.setattr(finder_pipeline, "extract_axes_for_document", fake_extract)

    def fake_retrieve(axes_a, axes_b, signal="cosine"):
        return [
            {
                "source_anchor_id": "ED 1",
                "target_anchor_id": "HKMA 1",
                "matched_axis_source": "consent",
                "matched_axis_target": "consent",
            }
        ]

    monkeypatch.setattr(finder_pipeline, "retrieve", fake_retrieve)

    def fake_call_chat(deployment, system, user, max_tokens=None):
        if system == finder_pipeline.SAME_TOPIC_FINDER_SYSTEM_PROMPT:
            deployments.append(("same_topic", deployment))
            return json.dumps(
                [
                    {
                        "summary": "both require consent",
                        "label": "differs-on",
                        "sentiment": "tighten",
                        "source_clauses": ["ED 1"],
                        "target_clauses": ["HKMA 1"],
                        "scope_note": "scoped to retail",
                    }
                ]
            )
        if system == finder_pipeline.COVERAGE_FINDER_SYSTEM_PROMPT:
            deployments.append(("coverage", deployment))
            return json.dumps(
                [
                    {
                        "summary": "ED goes beyond on authentication",
                        "label": "goes-beyond",
                        "source_clauses": ["ED 2"],
                        "target_clauses": [],
                    }
                ]
            )
        raise AssertionError(f"unexpected system prompt for deployment {deployment}")

    monkeypatch.setattr(finder_pipeline, "call_chat", fake_call_chat)


def test_output_contract_shape(monkeypatch, tmp_path):
    import engine.finder_pipeline as finder_pipeline

    deployments: list = []
    _install_orchestration_stubs(monkeypatch, tmp_path, deployments)

    result = finder_pipeline.run_finder_pipeline(_orchestration_index(), "doc-a", "doc-b")

    assert set(result.keys()) == {"connections", "unsupported", "trace"}
    assert "metadata" not in result
    # scope_note retained on connections.
    assert any(c.get("scope_note") == "scoped to retail" for c in result["connections"])

    trace = result["trace"]
    for key in (
        "retrieval_candidates",
        "same_topic_finder_output",
        "suppression",
        "coverage_finder_output",
        "validation",
        "citation_rewrites",
        "counts",
        "wall_clock_seconds",
    ):
        assert key in trace, f"trace missing {key}"

    # Each coverage entry carries computed single_sided / redundant.
    for entry in trace["coverage_finder_output"]:
        assert "single_sided" in entry
        assert "redundant" in entry
    counts = trace["counts"]
    assert counts["same_topic_finding"] == 1
    assert counts["coverage_finding"] == 1


def test_three_tier_routing_no_critic(monkeypatch, tmp_path):
    import engine.finder_pipeline as finder_pipeline

    deployments: list = []
    _install_orchestration_stubs(monkeypatch, tmp_path, deployments)

    finder_pipeline.run_finder_pipeline(_orchestration_index(), "doc-a", "doc-b")

    stages = {stage: dep for stage, dep in deployments}
    assert stages["extract"] == finder_pipeline.EXTRACTION_DEPLOYMENT
    assert stages["same_topic"] == finder_pipeline.REASONING_DEPLOYMENT
    assert stages["coverage"] == finder_pipeline.FINDER_CRITIC_DEPLOYMENT
    # Three distinct tiers, no critic stage ever recorded.
    assert "critic" not in stages
    assert (
        finder_pipeline.EXTRACTION_DEPLOYMENT
        != finder_pipeline.REASONING_DEPLOYMENT
        != finder_pipeline.FINDER_CRITIC_DEPLOYMENT
    )


# ---------------------------------------------------------------------------
# axes_dir parameter — the per-workstream axis cache location.
# ---------------------------------------------------------------------------


def test_axes_dir_writes_and_reads_outside_the_default_location(tmp_path, monkeypatch):
    """Passing `axes_dir` puts the cache there, NOT under the module default —
    this is what lets a workstream's axis cache travel with the workstream."""
    import engine.finder_pipeline as finder_pipeline

    default_dir = tmp_path / "default"
    ws_dir = tmp_path / "opres-v2" / "axes"
    monkeypatch.setattr(finder_pipeline, "AXES_DIR", default_dir)

    index = AnchorIndex([_anchor("DOC 1.1", "doc-a", "Some clause text.")])

    calls: list = []

    def fake_call_chat(deployment, system, user, max_tokens=None):
        calls.append(deployment)
        return json.dumps(["scenario testing cadence"])

    monkeypatch.setattr(finder_pipeline, "call_chat", fake_call_chat)

    result = finder_pipeline.extract_axes_for_document(index, "doc-a", axes_dir=ws_dir)

    assert result["DOC 1.1"] == ["scenario testing cadence"]
    assert (ws_dir / "axes-doc-a.json").exists()
    assert not (default_dir / "axes-doc-a.json").exists()
    assert len(calls) == 1

    # A second call against the same axes_dir is a cache hit — no model call.
    def boom(*args, **kwargs):
        raise AssertionError("cache hit must not call the model")

    monkeypatch.setattr(finder_pipeline, "call_chat", boom)
    again = finder_pipeline.extract_axes_for_document(index, "doc-a", axes_dir=ws_dir)
    assert again["DOC 1.1"] == ["scenario testing cadence"]


def test_axes_dir_defaults_to_the_module_location(tmp_path, monkeypatch):
    """Omitting axes_dir preserves the experiment/script path (back-compat)."""
    import engine.finder_pipeline as finder_pipeline

    monkeypatch.setattr(finder_pipeline, "AXES_DIR", tmp_path)
    index = AnchorIndex([_anchor("DOC 1.1", "doc-a", "Some clause text.")])
    monkeypatch.setattr(
        finder_pipeline,
        "call_chat",
        lambda *a, **k: json.dumps(["an axis"]),
    )

    finder_pipeline.extract_axes_for_document(index, "doc-a")

    assert (tmp_path / "axes-doc-a.json").exists()
