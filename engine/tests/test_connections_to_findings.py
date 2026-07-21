from engine.workstreams import connections_to_findings

CONN = {
    "summary": "Both require BCP.",
    "label": "aligns-with",
    "sentiment": None,
    "source_clauses": [{"clause_number": "Operational Resilience 4.3", "text": "..."}],
    "target_clauses": [{"clause_number": "Open Finance 7.6(b)", "text": "..."}],
    "scope_note": None,
    "supported": True,
}


def test_adds_id_and_pending_review_state():
    out = connections_to_findings({"connections": [CONN], "unsupported": []})
    assert len(out) == 1
    f = out[0]
    assert f["review_state"] == "pending"
    assert isinstance(f["id"], str) and f["id"]
    assert f["summary"] == CONN["summary"]
    assert f["source_clauses"] == CONN["source_clauses"]


def test_id_is_stable_for_same_connection():
    a = connections_to_findings({"connections": [CONN], "unsupported": []})[0]
    b = connections_to_findings({"connections": [CONN], "unsupported": []})[0]
    assert a["id"] == b["id"]


def test_excludes_unsupported():
    result = {"connections": [], "unsupported": [{"summary": "dropped"}]}
    assert connections_to_findings(result) == []
