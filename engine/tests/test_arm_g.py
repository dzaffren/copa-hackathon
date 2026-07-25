"""Tests for the Arm G finding pipeline (engine/arm_g.py).

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
    import engine.arm_g as arm_g

    monkeypatch.setattr(arm_g, "AXES_DIR", tmp_path)

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
                "text_hash": arm_g._text_hash(long_text),
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

    monkeypatch.setattr(arm_g, "call_chat", fake_call_chat)

    result = arm_g.extract_axes_for_document(index, "doc-a")

    # Cap change forced a re-extraction (one model call).
    assert len(calls) == 1
    assert result["DOC 1.1"] == ["fresh axis one", "fresh axis two"]

    # The entry is rewritten with the correct new cap.
    rewritten = json.loads((tmp_path / "axes-doc-a.json").read_text(encoding="utf-8"))
    entry = rewritten["anchors"][0]
    assert entry["axis_cap"] == arm_g._axis_cap(long_text)
    assert entry["axis_cap"] != 5
    assert entry["axes"] == ["fresh axis one", "fresh axis two"]


def test_axis_cache_hit_skips_extraction(tmp_path, monkeypatch):
    """When text_hash AND axis_cap both match, the entry is reused with no model
    call."""
    import engine.arm_g as arm_g

    monkeypatch.setattr(arm_g, "AXES_DIR", tmp_path)

    text = "A short clause about consent."
    index = AnchorIndex([_anchor("DOC 1.1", "doc-a", text)])

    fresh = {
        "document_id": "doc-a",
        "model": "m",
        "anchors": [
            {
                "anchor_id": "DOC 1.1",
                "text_hash": arm_g._text_hash(text),
                "axis_cap": arm_g._axis_cap(text),
                "axes": ["cached axis"],
            }
        ],
    }
    (tmp_path / "axes-doc-a.json").write_text(json.dumps(fresh), encoding="utf-8")

    def boom(*a, **k):  # pragma: no cover - must not be called
        raise AssertionError("call_chat should not run on a cache hit")

    monkeypatch.setattr(arm_g, "call_chat", boom)

    result = arm_g.extract_axes_for_document(index, "doc-a")
    assert result["DOC 1.1"] == ["cached axis"]


def test_axis_cap_scales_with_length():
    """A long dense anchor gets a higher cap than a short one, both bounded."""
    import engine.arm_g as arm_g

    short = arm_g._axis_cap("A single short sentence.")
    long = arm_g._axis_cap("x" * 4000)
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
    import engine.arm_g as arm_g

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

    monkeypatch.setattr(arm_g, "call_chat", fake_call_chat)

    findings = arm_g.finder_same_topic_batched(index, candidates)

    assert len(findings) == 1
    finding = findings[0]
    assert finding["source_clauses"] == ["ED 1"]
    assert finding["target_clauses"] == ["HKMA 2"]
    # Both sides of the batch union were shown to the finder.
    assert "ED 1" in captured_users[0] and "ED 2" in captured_users[0]
    assert "HKMA 1" in captured_users[0] and "HKMA 2" in captured_users[0]


def test_batch_partitions_anchors_by_side(monkeypatch):
    """The A-side list and B-side list are presented separately in the prompt."""
    import engine.arm_g as arm_g

    index = _stage3_index()
    candidates = _stage3_candidates()[:8]  # ED/HKMA 1..8

    captured = []

    def fake_call_chat(deployment, system, user, max_tokens=None):
        captured.append(user)
        return "[]"

    monkeypatch.setattr(arm_g, "call_chat", fake_call_chat)
    arm_g.finder_same_topic_batched(index, candidates)

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
    import engine.arm_g as arm_g

    index = _stage3_index()
    candidates = _stage3_candidates()[:8]

    calls = {"n": 0}

    def flaky_call_chat(deployment, system, user, max_tokens=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise arm_g.LLMResponseError("boom on first try")
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

    monkeypatch.setattr(arm_g, "call_chat", flaky_call_chat)

    findings = arm_g.finder_same_topic_batched(index, candidates)
    assert calls["n"] == 2  # one failure + one retry
    assert len(findings) == 1


def test_batch_failure_skips_and_logs_pair_ids(monkeypatch, caplog):
    """A batch that fails on both attempts is skipped, every pair id is logged,
    and the pipeline continues (returns findings from other batches)."""
    import logging

    import engine.arm_g as arm_g

    index = _stage3_index()
    # 8 candidates → a single batch, which always fails on both attempts.
    candidates = _stage3_candidates()[:8]

    def always_fails(deployment, system, user, max_tokens=None):
        raise arm_g.LLMResponseError("always fails")

    monkeypatch.setattr(arm_g, "call_chat", always_fails)

    with caplog.at_level(logging.WARNING):
        findings = arm_g.finder_same_topic_batched(index, candidates)

    assert findings == []  # the only batch was skipped
    # Every dropped pair id from the batch is logged.
    logged = "\n".join(r.message for r in caplog.records)
    assert "skipped after retry" in logged
    assert "ED 1 × HKMA 1" in logged
    assert "ED 8 × HKMA 8" in logged
