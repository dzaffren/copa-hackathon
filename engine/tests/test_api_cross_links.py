"""Tests for cross-workstream linkage.

The demo's climax: two BNM workstreams drafted in parallel by different teams,
and a linkage between them that neither team's members would find by reading
their own workstream. The findings are a projection of a real finder+critic run
(see data/workstreams/_cross/README.md), not fixtures.
"""

import json
import shutil

from fastapi.testclient import TestClient

from engine.api import create_app
from engine.config import REPO_ROOT

_CROSS_EDGE = "x-open_finance_ed--opres_dp_2025"
_OPRES = "opres-v2"
_OF = "open-finance-ed"


def _make_client(tmp_path):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    return TestClient(create_app(workstreams_dir=dst)), dst


def _links(client, workstream_id):
    return client.get(f"/api/workstreams/{workstream_id}/cross-links").json()["links"]


# --- discovery -------------------------------------------------------------


def test_opres_sees_the_link_into_open_finance(tmp_path):
    client, _ = _make_client(tmp_path)
    links = _links(client, _OPRES)

    assert len(links) == 1
    link = links[0]
    assert link["near"]["title"] == "OpRes DP (Dec 2025)"
    assert link["far"]["workstream_id"] == _OF
    assert link["far"]["workstream_name"] == "Open Finance ED · 2025"
    assert link["findings_count"] == 12


def test_open_finance_sees_the_same_link_from_its_own_end(tmp_path):
    """One stored edge, read from either side — the near/far flip."""
    client, _ = _make_client(tmp_path)
    link = _links(client, _OF)[0]

    assert link["id"] == _CROSS_EDGE
    assert link["near"]["title"] == "Open Finance ED — 18 Nov 2025"
    assert link["far"]["workstream_id"] == _OPRES
    assert link["far"]["workstream_name"] == "Operational Resilience v0.3"


def test_an_unrelated_workstream_sees_no_links(tmp_path):
    client, _ = _make_client(tmp_path)
    assert _links(client, "outsourcing-v2") == []


def test_link_carries_a_label_tally(tmp_path):
    """So a caller can render "12 linkages · 4 differ" without fetching each."""
    client, _ = _make_client(tmp_path)
    labels = _links(client, _OPRES)[0]["labels"]
    assert labels == {"aligns-with": 6, "differs-on": 4, "goes-beyond": 2}
    assert sum(labels.values()) == 12


def test_cross_links_404_for_an_unknown_workstream(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.get("/api/workstreams/nope/cross-links")
    assert res.status_code == 404
    assert res.json()["code"] == "WORKSTREAM_NOT_FOUND"


# --- the _cross store is not a workstream ----------------------------------


def test_cross_store_never_appears_in_the_sidebar(tmp_path):
    """It has no workstream.json, so list_workstreams skips it. If it ever
    gained one it would show up as a workstream the drafter can open, which it
    is not."""
    client, _ = _make_client(tmp_path)
    listed = [w["id"] for w in client.get("/api/workstreams").json()["workstreams"]]
    assert "_cross" not in listed
    assert _OF in listed and _OPRES in listed


def test_cross_store_has_no_workstream_json(tmp_path):
    _, dst = _make_client(tmp_path)
    assert not (dst / "_cross" / "workstream.json").exists()


# --- the existing review route serves it unchanged -------------------------


def test_the_ordinary_review_route_serves_the_cross_link(tmp_path):
    """No new read path: `_cross` uses the ordinary node/edge shape, so the
    review screen reads it like any other edge."""
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/workstreams/_cross/edges/{_CROSS_EDGE}/review").json()

    assert body["edge"]["source_node"]["title"] == "Open Finance ED — 18 Nov 2025"
    assert body["edge"]["target_node"]["title"] == "OpRes DP (Dec 2025)"
    assert len(body["findings"]) == 12
    assert body["counts"] == {"total": 12, "accepted": 0, "dismissed": 0}
    assert len(body["source_clauses"]) > 0 and len(body["target_clauses"]) > 0


def test_a_cross_finding_can_be_accepted_like_any_other(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.patch(
        f"/api/workstreams/_cross/edges/{_CROSS_EDGE}/findings/{_CROSS_EDGE}~0",
        json={"review_state": "accepted"},
    )
    assert res.status_code == 200
    assert res.json()["counts"]["accepted"] == 1


def test_accepting_a_cross_finding_bumps_the_link_counts(tmp_path):
    client, _ = _make_client(tmp_path)
    client.patch(
        f"/api/workstreams/_cross/edges/{_CROSS_EDGE}/findings/{_CROSS_EDGE}~0",
        json={"review_state": "accepted"},
    )
    assert _links(client, _OPRES)[0]["counts"]["accepted"] == 1


# --- the findings are real, and cited ---------------------------------------


def test_every_finding_is_verbatim_cited_from_both_sides_or_says_it_cannot_be(
    tmp_path,
):
    """The product rule, on the demo's own data.

    One clause — Operational Resilience 3.3(e) — does not resolve offline and
    renders as "No matching clause found". It is not dropped and not invented;
    the finding still shows that it cited something we cannot quote.
    """
    _, dst = _make_client(tmp_path)
    findings = json.loads(
        (dst / "_cross" / "findings" / f"{_CROSS_EDGE}.json").read_text(encoding="utf-8")
    )
    assert len(findings) == 12

    unquotable = []
    for finding in findings:
        assert finding["source_clauses"], f"{finding['summary'][:40]}: no source clause"
        assert finding["target_clauses"], f"{finding['summary'][:40]}: no target clause"
        for side in ("source_clauses", "target_clauses"):
            for clause in finding[side]:
                assert clause["clause_number"]
                assert clause["text"].strip()
                if clause["text"] == "No matching clause found":
                    unquotable.append(clause["clause_number"])

    # 10 of 63 clause citations cannot be quoted: one clause the offline
    # extractor never emits (3.3(e)), and nine it emits hollow (empty text).
    # Both render as "No matching clause found" — visible, not silently dropped.
    # A DI rebuild is what shrinks this; see MAX_HOLLOW in
    # test_artifact_integrity.py.
    assert sorted(set(unquotable)) == [
        "Operational Resilience 2.3",
        "Operational Resilience 2.5",
        "Operational Resilience 2.9(b)",
        "Operational Resilience 2.9(c)",
        "Operational Resilience 2.9(d)",
        "Operational Resilience 2.9(e)",
        "Operational Resilience 2.9(g)",
        "Operational Resilience 3.3(e)",
        "Operational Resilience 6.4(d)",
    ], f"Unquotable set changed: {sorted(set(unquotable))}"


def test_every_linkage_still_quotes_at_least_one_clause_per_side_except_one(tmp_path):
    """A linkage that can quote nothing on one side is not reviewable.

    Exactly one of the twelve is in that state: its OpRes side cites only
    2.9(e) and 3.3(e), both casualties of offline extraction. It is kept rather
    than dropped — the model really did find and cite it, and both clauses
    resolved when the run happened, so deleting it would misrepresent the
    engine's output to make the demo look tidier. Pinned at one so the rot
    cannot spread unnoticed.
    """
    _, dst = _make_client(tmp_path)
    findings = json.loads(
        (dst / "_cross" / "findings" / f"{_CROSS_EDGE}.json").read_text(encoding="utf-8")
    )
    mute = [
        i
        for i, f in enumerate(findings)
        for side in ("source_clauses", "target_clauses")
        if all(c["text"] == "No matching clause found" for c in f[side])
    ]
    assert mute == [5], f"Expected exactly finding[5] to have a mute side, got {mute}"


def test_findings_use_only_the_five_label_taxonomy(tmp_path):
    _, dst = _make_client(tmp_path)
    findings = json.loads(
        (dst / "_cross" / "findings" / f"{_CROSS_EDGE}.json").read_text(encoding="utf-8")
    )
    allowed = {"aligns-with", "differs-on", "conflicts-with", "silent-on", "goes-beyond"}
    assert {f["label"] for f in findings} <= allowed
    # sentiment is valid only on differs-on
    for f in findings:
        if f["label"] != "differs-on":
            assert f.get("sentiment") is None, f["summary"][:40]


def test_the_accountability_gap_survived_the_projection(tmp_path):
    """The brief's demo-hero linkage: Open Finance mandates board oversight but
    no single accountable person, where the OpRes DP has Responsibility Mapping.
    Pinned because it is the moment the demo turns on."""
    _, dst = _make_client(tmp_path)
    findings = json.loads(
        (dst / "_cross" / "findings" / f"{_CROSS_EDGE}.json").read_text(encoding="utf-8")
    )
    gap = next(f for f in findings if f["label"] == "goes-beyond" and "7.1" in json.dumps(f))
    assert "Open Finance 7.1" in [c["clause_number"] for c in gap["source_clauses"]]
    assert "Operational Resilience 6.3" in [
        c["clause_number"] for c in gap["target_clauses"]
    ]
    assert "accountab" in (gap["scope_note"] or "").lower()
