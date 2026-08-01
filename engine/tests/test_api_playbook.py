"""The Playbook: the drafter's per-stage instructions for the Copilot.

Same fixture discipline as the sibling suites — each test copies the seeded
`data/workstreams/` into `tmp_path`, so reads double as integrity checks on the
real fixtures while writes touch only the throwaway copy.

Three properties are easy to "improve" into a bug and are guarded hardest:

1. **A read never writes.** Serving four empty sections must not create a file,
   or reading a retired fixture's playbook would mutate recorded history.
2. **`/explore-task` has no field.** That stage reports what a document's profile
   records; an editable override would let the tool state a regulatory identity
   the document does not have. A client sending one is ignored, not rejected.
3. **The change is ADDITIVE.** With no `stage` in the request, the Copilot's
   system prompt must be byte-identical to the one it produced before playbooks
   existed — see `test_no_stage_leaves_the_system_prompt_untouched`, which is the
   regression guard for the whole feature.
"""

import json
import shutil

from fastapi.testclient import TestClient

from engine import playbook
from engine.api import create_app
from engine.config import REPO_ROOT
from engine.copilot import _system_prompt

_WS = "open-finance-pd-2026"
_TASK = "open-finance-pd-2026-pd"
_RETIRED = "opres-v2"


def _make_client(tmp_path):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    # The demo workstream SHIPS a playbook (build-and-persist, per CLAUDE.md), so
    # a test asserting the unsaved state has to create that state explicitly
    # rather than assume it. Scrubs the tmp copy only.
    for path in dst.glob("*/playbook.json"):
        path.unlink()
    return TestClient(create_app(workstreams_dir=dst)), dst


def _url(workstream_id=_WS):
    return f"/api/workstreams/{workstream_id}/playbook"


def _full(**overrides):
    body = {
        "brainstorm": "Should consent expiry differ for business customers?",
        "draft": "Follow the standard PD skeleton, numbering standards as S 1.1.",
        "write": 'Obligations read "must". Guidance reads "should".',
        "deliver": "Policy sign-off first, then Legal, then the DG's office.",
    }
    body.update(overrides)
    return body


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------


def test_an_unsaved_playbook_is_four_empty_sections_and_writes_nothing(tmp_path):
    """Test 1: every section starts empty, and reading creates no file.

    Unlike the guardrails there are no shipped defaults — the Copilot's current
    behaviour is the baseline, and pre-filled text a drafter did not write would
    be followed silently.
    """
    client, workstreams_dir = _make_client(tmp_path)
    path = playbook.playbook_path(workstreams_dir, _WS)
    assert not path.exists()

    response = client.get(_url())

    assert response.status_code == 200
    body = response.json()
    assert body["is_default"] is True
    assert body["updated_at"] is None
    for section in playbook.SECTIONS:
        assert body[section] == ""
    assert not path.exists(), "a read must never create the file"


def test_the_playbook_round_trips(tmp_path):
    """Test 2: what she saves is what she gets back."""
    client, workstreams_dir = _make_client(tmp_path)

    saved = client.put(_url(), json=_full())

    assert saved.status_code == 200
    assert saved.json()["is_default"] is False
    assert saved.json()["updated_at"] is not None
    assert saved.json()["write"] == 'Obligations read "must". Guidance reads "should".'

    reread = client.get(_url()).json()
    for section in playbook.SECTIONS:
        assert reread[section] == _full()[section]

    on_disk = json.loads(
        playbook.playbook_path(workstreams_dir, _WS).read_text(encoding="utf-8")
    )
    assert on_disk["brainstorm"] == _full()["brainstorm"]


def test_a_save_is_a_full_replacement(tmp_path):
    """Test 3: a section the client omits lands empty.

    The form always sends all four, so an omission is the drafter clearing it —
    leaving the stored value would show her something she had just deleted.
    """
    client, _workstreams_dir = _make_client(tmp_path)
    client.put(_url(), json=_full())

    response = client.put(_url(), json={"write": "Obligations read must."})

    assert response.status_code == 200
    body = response.json()
    assert body["write"] == "Obligations read must."
    assert body["brainstorm"] == ""
    assert body["draft"] == ""
    assert body["deliver"] == ""


def test_explore_task_is_ignored_not_rejected(tmp_path):
    """Test 4: the locked stage has no field, and sending one is not an error.

    Ignoring rather than rejecting matches how `_parse_copilot_request` treats a
    stale `intent` — a client should not get a 400 for a field the server no
    longer wants.
    """
    client, workstreams_dir = _make_client(tmp_path)

    response = client.put(
        _url(),
        json={"brainstorm": "q", "explore_task": "override the profile"},
    )

    assert response.status_code == 200
    assert response.json()["brainstorm"] == "q"
    assert "explore_task" not in response.json()
    on_disk = json.loads(
        playbook.playbook_path(workstreams_dir, _WS).read_text(encoding="utf-8")
    )
    assert "explore_task" not in on_disk


def test_a_non_string_section_is_refused_with_its_field_name(tmp_path):
    """Test 5: the form rings the offending textarea, not a banner."""
    client, workstreams_dir = _make_client(tmp_path)
    client.put(_url(), json=_full())
    before = playbook.playbook_path(workstreams_dir, _WS).read_bytes()

    response = client.put(_url(), json={"write": ["a list"]})

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_PLAYBOOK"
    assert response.json()["message"] == "write must be a string."
    assert response.json()["field"] == "write"
    assert playbook.playbook_path(workstreams_dir, _WS).read_bytes() == before


def test_an_oversized_section_is_refused_with_its_field_name(tmp_path):
    """Test 6: 20 000 characters per section, and the cap names the section."""
    client, _workstreams_dir = _make_client(tmp_path)

    response = client.put(
        _url(), json={"draft": "x" * (playbook.MAX_SECTION_CHARS + 1)}
    )

    assert response.status_code == 413
    assert response.json()["code"] == "PLAYBOOK_TOO_LARGE"
    assert response.json()["message"] == "draft holds at most 20000 characters."
    assert response.json()["field"] == "draft"


def test_a_section_exactly_at_the_cap_is_accepted(tmp_path):
    """The boundary is inclusive, or a legitimate paste is refused off-by-one."""
    client, _workstreams_dir = _make_client(tmp_path)

    response = client.put(
        _url(), json={"write": "y" * playbook.MAX_SECTION_CHARS}
    )

    assert response.status_code == 200
    assert len(response.json()["write"]) == playbook.MAX_SECTION_CHARS


def test_a_non_object_body_is_refused(tmp_path):
    """Test 7."""
    client, _workstreams_dir = _make_client(tmp_path)

    response = client.put(_url(), json=["not", "an", "object"])

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_PLAYBOOK"


def test_an_unknown_workstream_is_a_404_on_both_verbs(tmp_path):
    """Test 8."""
    client, workstreams_dir = _make_client(tmp_path)

    assert client.get(_url("no-such-ws")).status_code == 404
    put = client.put(_url("no-such-ws"), json=_full())
    assert put.status_code == 404
    assert put.json()["code"] == "WORKSTREAM_NOT_FOUND"
    assert not (workstreams_dir / "no-such-ws").exists()


def test_a_traversal_in_the_workstream_id_is_refused_before_any_write(tmp_path):
    """Test 9: the 404 guard is the security boundary — `playbook_path`
    interpolates `workstream_id` into a filesystem path."""
    client, workstreams_dir = _make_client(tmp_path)

    response = client.put("/api/workstreams/..%2F..%2Fetc/playbook", json=_full())

    assert response.status_code == 404
    assert not (workstreams_dir.parent / "playbook.json").exists()


def test_playbooks_are_per_workstream_and_retired_fixtures_stay_clean(tmp_path):
    """Test 10: a convention for one policy area must not silently govern another,
    and reading a retired fixture's playbook creates nothing inside it."""
    client, workstreams_dir = _make_client(tmp_path)
    client.put(_url(), json=_full())

    other = client.get(_url(_RETIRED))

    assert other.status_code == 200
    assert other.json()["is_default"] is True
    assert other.json()["write"] == ""
    assert not playbook.playbook_path(workstreams_dir, _RETIRED).exists()


def test_clearing_every_section_is_a_valid_save(tmp_path):
    """An empty playbook is a real state — the Copilot simply behaves as it does
    today. Nothing reinstates anything, because there are no defaults to reinstate."""
    client, _workstreams_dir = _make_client(tmp_path)
    client.put(_url(), json=_full())

    emptied = client.put(_url(), json={s: "" for s in playbook.SECTIONS})

    assert emptied.status_code == 200
    assert emptied.json()["is_default"] is False
    for section in playbook.SECTIONS:
        assert emptied.json()[section] == ""


# ---------------------------------------------------------------------------
# Injection into the Copilot's system prompt
# ---------------------------------------------------------------------------


def test_the_running_stages_section_reaches_the_prompt(tmp_path):
    """Test 11."""
    _client, workstreams_dir = _make_client(tmp_path)
    playbook.save(workstreams_dir, _WS, {"write": "Obligations read must."})

    section = playbook.section_for_stage(workstreams_dir, _WS, "/write")
    prompt = _system_prompt("T", "PD", "ctx", section)

    assert "Obligations read must." in prompt
    assert "PLAYBOOK" in prompt


def test_only_the_running_stages_section_is_injected(tmp_path):
    """Test 12: `/deliver`'s approval layers must not influence `/draft`."""
    _client, workstreams_dir = _make_client(tmp_path)
    playbook.save(
        workstreams_dir,
        _WS,
        {
            "brainstorm": "BRAINSTORM_MARKER",
            "draft": "DRAFT_MARKER",
            "write": "WRITE_MARKER",
            "deliver": "DELIVER_MARKER",
        },
    )

    prompt = _system_prompt(
        "T", "PD", "ctx", playbook.section_for_stage(workstreams_dir, _WS, "/draft")
    )

    assert "DRAFT_MARKER" in prompt
    for absent in ("BRAINSTORM_MARKER", "WRITE_MARKER", "DELIVER_MARKER"):
        assert absent not in prompt


def test_an_empty_section_adds_no_block(tmp_path):
    """Test 13."""
    _client, workstreams_dir = _make_client(tmp_path)
    playbook.save(workstreams_dir, _WS, {"write": ""})

    section = playbook.section_for_stage(workstreams_dir, _WS, "/write")

    assert section == ""
    assert "PLAYBOOK" not in _system_prompt("T", "PD", "ctx", section)


def test_no_stage_leaves_the_system_prompt_untouched(tmp_path):
    """Test 14: the change is ADDITIVE.

    The regression guard for the whole feature. With no `stage` the prompt must be
    string-equal to the one produced with no playbook at all — otherwise a later
    edit could reorder or pad the prompt and no existing test would notice.
    """
    _client, workstreams_dir = _make_client(tmp_path)
    playbook.save(workstreams_dir, _WS, _full())

    with_playbook_but_no_stage = _system_prompt(
        "T", "PD", "ctx", playbook.section_for_stage(workstreams_dir, _WS, None)
    )
    baseline = _system_prompt("T", "PD", "ctx")

    assert with_playbook_but_no_stage == baseline


def test_explore_task_and_unrecognised_stages_inject_nothing(tmp_path):
    """Tests 15 and 16: the locked stage selects nothing, and a nonsense stage is
    ignored rather than erroring."""
    _client, workstreams_dir = _make_client(tmp_path)
    playbook.save(workstreams_dir, _WS, _full())

    for stage in ("/explore-task", "explore-task", "nonsense", "", None):
        assert playbook.section_for_stage(workstreams_dir, _WS, stage) == ""


def test_a_bare_stage_name_resolves_like_its_slash_form(tmp_path):
    """A client sending "write" rather than "/write" means the same thing;
    refusing it would be pedantry."""
    _client, workstreams_dir = _make_client(tmp_path)
    playbook.save(workstreams_dir, _WS, {"write": "House rule."})

    assert (
        playbook.section_for_stage(workstreams_dir, _WS, "write")
        == playbook.section_for_stage(workstreams_dir, _WS, "/write")
        == "House rule."
    )


def test_the_playbook_block_sits_after_the_citation_rules(tmp_path):
    """Test 17: a playbook instruction shapes how the Copilot writes; it cannot
    loosen what it may cite. Position is the structural expression of that, and
    `_validate_reply` enforces the citations regardless."""
    _client, workstreams_dir = _make_client(tmp_path)
    playbook.save(
        workstreams_dir, _WS, {"write": "Quote any clause you find useful."}
    )

    prompt = _system_prompt(
        "T", "PD", "ctx", playbook.section_for_stage(workstreams_dir, _WS, "/write")
    )

    assert prompt.index("PLAYBOOK") > prompt.index("GROUNDING AND CITATION RULES")


def test_the_stage_reaches_the_copilot_route(tmp_path):
    """End to end through the route: `stage` in the body selects the section that
    reaches the injected seam."""
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    captured: dict[str, str] = {}

    def _stub(**kwargs):
        captured["section"] = kwargs.get("playbook_section", "")
        return {"text": "ok", "citations": [], "snippet_html": None}

    client = TestClient(create_app(workstreams_dir=dst, copilot_reply_fn=_stub))
    playbook.save(dst, _WS, {"write": "ROUTE_MARKER"})

    response = client.post(
        f"/api/workstreams/{_WS}/tasks/{_TASK}/copilot",
        json={"message": "Draft clause 3.1", "stage": "/write"},
    )

    assert response.status_code == 200
    assert captured["section"] == "ROUTE_MARKER"


def test_a_copilot_request_with_no_stage_gets_no_section(tmp_path):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    captured: dict[str, str] = {}

    def _stub(**kwargs):
        captured["section"] = kwargs.get("playbook_section", "")
        return {"text": "ok", "citations": [], "snippet_html": None}

    client = TestClient(create_app(workstreams_dir=dst, copilot_reply_fn=_stub))
    playbook.save(dst, _WS, _full())

    client.post(
        f"/api/workstreams/{_WS}/tasks/{_TASK}/copilot",
        json={"message": "Anything"},
    )

    assert captured["section"] == ""
