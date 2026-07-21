"""Unit tests for the Cross-Workstream Intelligence derivation (pure module).

`engine.cross_intel` is the "why do these two workstreams overlap" logic: shared
attributes, plain-language reasons, and a classification/risk rollup of the
five-label taxonomy. It takes plain concept dicts, so it needs no fixtures.
"""

from engine import cross_intel

_BCM = {
    "policy_owner": "Jarod N.",
    "applicability": "Licensed banks, licensed Islamic banks and licensed investment banks",
    "keywords": ["business continuity", "continuity of critical functions", "recovery time objective"],
    "legal_basis": ["FSA 2013", "IFSA 2013", "DFIA 2002"],
    "ismp_classification": None,
}
_RRP = {
    "policy_owner": "Priya S.",
    "applicability": "Licensed banks, licensed Islamic banks and licensed investment banks",
    "keywords": ["recovery planning", "continuity of critical functions", "recovery options"],
    "legal_basis": ["FSA 2013", "IFSA 2013"],
    "ismp_classification": None,
}


# --- shared attributes ------------------------------------------------------


def test_shared_legal_basis_is_the_case_insensitive_intersection():
    assert cross_intel.shared_legal_basis(_BCM, _RRP) == ["FSA 2013", "IFSA 2013"]


def test_shared_keywords_finds_the_common_topic():
    assert cross_intel.shared_keywords(_BCM, _RRP) == ["continuity of critical functions"]


def test_shared_applicability_matches_controlled_vocabulary():
    shared = cross_intel.shared_applicability(_BCM, _RRP)
    assert "licensed banks" in shared
    assert "licensed Islamic banks" in shared


def test_shared_applicability_empty_when_one_side_is_null():
    assert cross_intel.shared_applicability(_BCM, {"applicability": None}) == []


def test_shared_policy_owner_none_when_owners_differ():
    assert cross_intel.shared_scalar(_BCM, _RRP, "policy_owner") is None


def test_shared_policy_owner_fires_when_equal():
    assert cross_intel.shared_scalar(_RRP, dict(_RRP), "policy_owner") == "Priya S."


def test_ismp_never_fires_while_unsourced():
    """Both null → no shared-ISMP claim. The field is honoured, not faked."""
    assert cross_intel.shared_scalar(_BCM, _RRP, "ismp_classification") is None


# --- classification / risk --------------------------------------------------


def test_conflict_is_high_risk():
    assert cross_intel.classify({"conflicts-with": 1, "aligns-with": 5}) == ("conflict", "high")


def test_differs_on_is_divergent_medium():
    assert cross_intel.classify({"differs-on": 4, "aligns-with": 6, "goes-beyond": 2}) == (
        "divergent",
        "medium",
    )


def test_only_aligns_is_aligned_low():
    assert cross_intel.classify({"aligns-with": 3}) == ("aligned", "low")


def test_empty_tally_is_unclassified_overlap():
    assert cross_intel.classify({}) == ("overlap", "low")


# --- reasons ----------------------------------------------------------------


def test_reasons_lead_with_shared_facts_then_label_rollup():
    shared = cross_intel.shared_attributes(_BCM, _RRP)
    labels = {"aligns-with": 6, "differs-on": 4, "goes-beyond": 2}
    lines = cross_intel.reasons(shared, labels)
    assert any("apply to licensed banks" in ln for ln in lines)
    assert any("issued under FSA 2013" in ln for ln in lines)
    assert any("continuity of critical functions" in ln for ln in lines)
    # label rollup lines appear too
    assert any("differ on 4 requirement" in ln for ln in lines)
    assert any("goes beyond" in ln for ln in lines)
    # owners differ, so no shared-owner line is invented
    assert not any("owned by" in ln for ln in lines)


def test_reasons_empty_when_nothing_shared_and_no_labels():
    assert cross_intel.reasons({}, {}) == []
