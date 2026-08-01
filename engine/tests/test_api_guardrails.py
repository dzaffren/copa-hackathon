"""The guardrails box: the rules the recommendations engine follows.

Same fixture discipline as `test_api_pairwise_findings.py` — each test copies the
seeded `data/workstreams/` into `tmp_path`, so reads double as integrity checks
on the real fixtures while writes touch only the throwaway copy.

The two properties worth guarding hardest, because both are easy to "improve"
into a bug:

1. **A read never writes.** Serving the defaults must not create a file, or
   reading a retired fixture's guardrails would mutate a fixture the
   retired-fixtures rule says is recorded history.
2. **An empty body stays empty.** Clearing the box is a deliberate act. Falling
   back to the defaults on an empty save would silently overrule the drafter and
   look like the feature working.
"""

import json
import shutil

from fastapi.testclient import TestClient

from engine import guardrails
from engine.api import create_app
from engine.config import REPO_ROOT

_WS = "open-finance-pd-2026"
_RETIRED = "opres-v2"


def _make_client(tmp_path):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    return TestClient(create_app(workstreams_dir=dst)), dst


def _url(workstream_id=_WS):
    return f"/api/workstreams/{workstream_id}/guardrails"


def test_the_defaults_are_served_when_nothing_has_been_saved(tmp_path):
    """Test 16: the box ships populated, and reading it writes nothing.

    An empty box on day one would be a feature nobody uses. The five defaults
    come from real reviewer evidence, so they are worth reading before they are
    worth changing.
    """
    client, workstreams_dir = _make_client(tmp_path)
    path = guardrails.guardrails_path(workstreams_dir, _WS)
    assert not path.exists()

    response = client.get(_url())

    assert response.status_code == 200
    body = response.json()
    assert body["is_default"] is True
    assert body["updated_at"] is None
    # All five rules present, by their distinguishing subject matter.
    assert "provision number" in body["body"]
    assert "applicability" in body["body"]
    assert "shared acronym" in body["body"]
    assert "neither elaborates" in body["body"]
    assert "word-for-word" in body["body"]
    assert not path.exists(), "a read must never create the file"


def test_guardrails_round_trip_and_stop_being_default(tmp_path):
    """Test 17 (storage half): what she saves is what she gets back."""
    client, workstreams_dir = _make_client(tmp_path)
    rule = (
        "HKMA's \"TSP\" corresponds to Malaysia's data consumer, not our TPSP — "
        "do not assert a gap on the shared acronym."
    )

    saved = client.put(_url(), json={"body": rule})

    assert saved.status_code == 200
    assert saved.json()["body"] == rule
    assert saved.json()["is_default"] is False
    assert saved.json()["updated_at"] is not None

    reread = client.get(_url())
    assert reread.json()["body"] == rule
    assert reread.json()["is_default"] is False

    on_disk = json.loads(
        guardrails.guardrails_path(workstreams_dir, _WS).read_text(encoding="utf-8")
    )
    assert on_disk["body"] == rule


def test_an_empty_body_is_accepted_and_stays_empty(tmp_path):
    """Test 18: clearing the box is deliberate; the defaults do not creep back.

    The failure this guards against reads as the feature working — a drafter
    empties the guardrails, the tool quietly reinstates five rules, and her next
    generation follows rules she deleted.
    """
    client, _ = _make_client(tmp_path)
    client.put(_url(), json={"body": "Something first."})

    emptied = client.put(_url(), json={"body": ""})

    assert emptied.status_code == 200
    assert emptied.json()["body"] == ""
    assert emptied.json()["is_default"] is False

    reread = client.get(_url())
    assert reread.json()["body"] == ""
    assert reread.json()["is_default"] is False


def test_an_oversized_body_is_refused_and_nothing_is_written(tmp_path):
    """Test 19: 20 000 characters is the cap, and a rejection changes nothing."""
    client, workstreams_dir = _make_client(tmp_path)
    client.put(_url(), json={"body": "Keep this."})
    before = guardrails.guardrails_path(workstreams_dir, _WS).read_bytes()

    response = client.put(
        _url(), json={"body": "x" * (guardrails.MAX_GUARDRAILS_CHARS + 1)}
    )

    assert response.status_code == 413
    assert response.json()["code"] == "GUARDRAILS_TOO_LARGE"
    assert response.json()["message"] == "Guardrails hold at most 20000 characters."
    assert guardrails.guardrails_path(workstreams_dir, _WS).read_bytes() == before


def test_a_body_at_the_cap_is_accepted(tmp_path):
    """The boundary is inclusive — exactly at the cap must save, or the limit is
    off by one and a legitimate paste is refused."""
    client, _ = _make_client(tmp_path)

    response = client.put(
        _url(), json={"body": "y" * guardrails.MAX_GUARDRAILS_CHARS}
    )

    assert response.status_code == 200
    assert len(response.json()["body"]) == guardrails.MAX_GUARDRAILS_CHARS


def test_a_non_string_body_is_refused(tmp_path):
    """Test 20: the field is free text, not a list of rules."""
    client, _ = _make_client(tmp_path)

    for bad in (["a", "b"], 42, None, {"nested": "object"}):
        response = client.put(_url(), json={"body": bad})
        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_GUARDRAILS"
        assert response.json()["message"] == "body must be a string."


def test_a_body_missing_the_key_entirely_is_refused(tmp_path):
    client, _ = _make_client(tmp_path)

    response = client.put(_url(), json={"guardrails": "wrong key"})

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_GUARDRAILS"


def test_guardrails_are_per_workstream_and_retired_fixtures_stay_clean(tmp_path):
    """Test 21: a rule saved in one workstream does not reach another, and
    reading a retired fixture's guardrails creates nothing inside it.

    The second half is the retired-fixtures rule (`CLAUDE.md`) applied to a new
    file: those workstreams are recorded history, and the engine suite reads
    several of them by id.
    """
    client, workstreams_dir = _make_client(tmp_path)
    client.put(_url(), json={"body": "Only for open finance."})

    other = client.get(_url(_RETIRED))

    assert other.status_code == 200
    assert other.json()["is_default"] is True
    assert "Only for open finance." not in other.json()["body"]
    assert not guardrails.guardrails_path(workstreams_dir, _RETIRED).exists()


def test_an_unknown_workstream_is_a_404_on_both_verbs(tmp_path):
    client, workstreams_dir = _make_client(tmp_path)

    assert client.get(_url("no-such-ws")).status_code == 404
    assert client.get(_url("no-such-ws")).json()["code"] == "WORKSTREAM_NOT_FOUND"

    put = client.put(_url("no-such-ws"), json={"body": "anything"})
    assert put.status_code == 404
    assert put.json()["code"] == "WORKSTREAM_NOT_FOUND"
    assert not (workstreams_dir / "no-such-ws").exists()


def test_a_traversal_in_the_workstream_id_is_refused_before_any_write(tmp_path):
    """The 404 guard is the security boundary, not a courtesy: `guardrails_path`
    interpolates `workstream_id` into a filesystem path."""
    client, workstreams_dir = _make_client(tmp_path)

    response = client.put(
        "/api/workstreams/..%2F..%2Fetc/guardrails", json={"body": "pwned"}
    )

    assert response.status_code == 404
    assert not (workstreams_dir.parent / "guardrails.json").exists()


def test_repeated_identical_saves_are_idempotent_in_content(tmp_path):
    """The same body twice yields the same body — only the timestamp moves."""
    client, _ = _make_client(tmp_path)
    rule = "Stay inside the draft's stated applicability."

    first = client.put(_url(), json={"body": rule}).json()
    second = client.put(_url(), json={"body": rule}).json()

    assert first["body"] == second["body"] == rule
    assert second["is_default"] is False


def test_body_for_prompt_reads_what_stands_right_now(tmp_path):
    """The prompt helper reflects the current file, so an edit takes effect on the
    next generation with nothing to invalidate."""
    _, workstreams_dir = _make_client(tmp_path)

    assert guardrails.body_for_prompt(workstreams_dir, _WS) == (
        guardrails.DEFAULT_GUARDRAILS
    )

    guardrails.save(workstreams_dir, _WS, "One rule only.")
    assert guardrails.body_for_prompt(workstreams_dir, _WS) == "One rule only."

    guardrails.save(workstreams_dir, _WS, "")
    assert guardrails.body_for_prompt(workstreams_dir, _WS) == ""
