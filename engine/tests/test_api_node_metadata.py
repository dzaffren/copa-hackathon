"""Node-detail regulatory metadata: legal basis, ISMP classification, the
supervisory-letter document type, and the drafter's own edits to the profile.

Phase 2 surfaces `legal_basis` and `ismp_classification` (added to the concept
sidecar) through the node-detail route, and confirms the supervisory-letter node
type is first-class end to end.

The write side (`PUT .../nodes/{node_id}/metadata`) lets the drafter record what
she knows about any document in any workstream. It is a full replacement of the
nine-field profile, not a patch, and every rejection happens before any
filesystem write.
"""

import json
import shutil

import pytest
from fastapi.testclient import TestClient

from engine import concepts
from engine.api import create_app
from engine.concepts import CONCEPT_FIELDS, concepts_path
from engine.config import REPO_ROOT


def _make_client(tmp_path):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    return TestClient(create_app(workstreams_dir=dst)), dst


def _metadata_url(workstream_id, node_id):
    return f"/api/workstreams/{workstream_id}/nodes/{node_id}/metadata"


def test_supervisory_letter_is_a_first_class_node_type_with_a_profile(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.get(
        "/api/workstreams/rmit-v2-2025/nodes/bnm-supervisory-letter-rmit-2025"
    ).json()
    assert body["node_type"] == "supervisory-letter"
    # The seven-field regulatory profile now lands under `metadata`; `concepts`
    # carries extracted axes.
    concepts = body["metadata"]
    assert concepts["status"] == "available"
    assert concepts["applicability"].startswith("Financial institutions")
    # An honest profile: no invented legal basis or classification for a letter.
    assert concepts["legal_basis"] is None
    assert concepts["ismp_classification"] is None


def test_new_concept_fields_are_present_for_every_enriched_document(tmp_path):
    """legal_basis + ismp_classification round-trip through save/load for the
    documents enriched in Phase 1/2, so the intelligence layer can rely on them."""
    client, _ = _make_client(tmp_path)
    for ws, node in [
        ("open-finance-ed", "of-ed-2025"),
        ("opres-v2", "opres-pd-v0-3"),
    ]:
        concepts = client.get(f"/api/workstreams/{ws}/nodes/{node}").json()["metadata"]
        assert concepts["status"] == "available"
        assert "legal_basis" in concepts
        assert "ismp_classification" in concepts


def test_a_first_save_creates_the_side_file(tmp_path):
    """Test 1: a node nobody prepared has no side-file; the first save makes one.

    Absence is the ordinary case, not an error — the drafter opens a document
    with an empty profile and fills in the two fields she is confident about.
    """
    client, workstreams_dir = _make_client(tmp_path)
    path = concepts_path(workstreams_dir, "open-finance-pd-2026", "bis-papers-168")
    assert not path.exists()

    response = client.put(
        _metadata_url("open-finance-pd-2026", "bis-papers-168"),
        json={
            "policy_owner": "Priya S.",
            "applicability": None,
            "empowerment_framework": None,
            "issuance_date": None,
            "effective_date": None,
            "legal_basis": ["FSA 2013"],
            "ismp_classification": None,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["node_id"] == "bis-papers-168"
    assert body["metadata"]["status"] == "available"
    assert body["metadata"]["policy_owner"] == "Priya S."
    assert body["metadata"]["legal_basis"] == ["FSA 2013"]

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert list(saved) == list(CONCEPT_FIELDS)
    # policy_owner and legal_basis were sent; the other five stay unset.
    assert sum(1 for value in saved.values() if value is None) == 5


def test_a_save_overwrites_an_existing_profile_whole(tmp_path):
    """Test 2: a save is a full replacement, not a patch.

    Deliberate: the form always sends all nine fields, so a field absent from the
    body is one the drafter cleared — leaving the stored value in place would show
    her something she had just deleted.

    The fixture's `rmit-pd-v2` profile carries only `policy_owner`, so this fills
    it out first; a replacement is only observable against a populated profile.
    """
    client, workstreams_dir = _make_client(tmp_path)
    path = concepts_path(workstreams_dir, "rmit-v2-2025", "rmit-pd-v2")
    assert json.loads(path.read_text(encoding="utf-8"))["policy_owner"] == "Aisyah R."

    populated = client.put(
        _metadata_url("rmit-v2-2025", "rmit-pd-v2"),
        json={
            "policy_owner": "Aisyah R.",
            "applicability": "Licensed banks.",
            "empowerment_framework": "Issued pursuant to section 143(2) of the FSA 2013.",
            "issuance_date": "28 November 2025",
            "effective_date": "28 November 2025",
            "legal_basis": ["FSA 2013"],
            "ismp_classification": "TERHAD",
        },
    )
    assert populated.status_code == 200
    assert all(value is not None for value in populated.json()["metadata"].values())

    response = client.put(
        _metadata_url("rmit-v2-2025", "rmit-pd-v2"),
        json={"policy_owner": "Farid M."},
    )

    assert response.status_code == 200
    metadata = response.json()["metadata"]
    assert metadata["policy_owner"] == "Farid M."
    assert [metadata[field] for field in CONCEPT_FIELDS if field != "policy_owner"] == [
        None
    ] * (len(CONCEPT_FIELDS) - 1)


def test_saved_values_round_trip_through_the_node_detail_route(tmp_path):
    """Test 3: what she saves is what she sees when she comes back.

    The claim of the whole story is persistence, so the read path has to be the
    one asserted against — not just the PUT's own echo of its input.
    """
    client, _ = _make_client(tmp_path)
    client.put(
        _metadata_url("open-finance-pd-2026", "bis-papers-168"),
        json={"policy_owner": "Priya S.", "legal_basis": ["FSA 2013"]},
    )

    body = client.get(
        "/api/workstreams/open-finance-pd-2026/nodes/bis-papers-168"
    ).json()

    assert body["metadata"]["status"] == "available"
    assert body["metadata"]["legal_basis"] == ["FSA 2013"]
    assert body["metadata"]["policy_owner"] == "Priya S."


def test_an_unknown_key_is_refused_and_nothing_is_written(tmp_path):
    """Test 4: a typo'd key is named, not silently dropped.

    Dropping it would lose the drafter's edit without telling her — she would
    save, see the field empty, and have no way to know why.
    """
    client, workstreams_dir = _make_client(tmp_path)
    path = concepts_path(workstreams_dir, "open-finance-pd-2026", "bis-papers-168")

    response = client.put(
        _metadata_url("open-finance-pd-2026", "bis-papers-168"),
        json={"policy_owner_name": "Aisyah R."},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "UNKNOWN_METADATA_FIELD"
    assert response.json()["field"] == "policy_owner_name"
    assert not path.exists()


def test_task_type_in_the_body_is_refused_as_immutable(tmp_path):
    """Test 5: the deliverable kind is set at creation and cannot be changed here.

    Refused rather than ignored, and with its own code rather than
    UNKNOWN_METADATA_FIELD: `task_type` is a real field, it just is not this
    route's to write.
    """
    client, workstreams_dir = _make_client(tmp_path)
    path = concepts_path(workstreams_dir, "open-finance-pd-2026", "bis-papers-168")

    response = client.put(
        _metadata_url("open-finance-pd-2026", "bis-papers-168"),
        json={"task_type": "FAQ", "policy_owner": "Aisyah R."},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "TASK_TYPE_IMMUTABLE"
    assert response.json()["field"] == "task_type"
    assert not path.exists()


def test_a_wrong_typed_scalar_field_is_refused(tmp_path):
    """Test 6: a scalar field takes a string or null, and says which field failed."""
    client, _ = _make_client(tmp_path)

    response = client.put(
        _metadata_url("open-finance-pd-2026", "bis-papers-168"),
        json={"policy_owner": 42},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_METADATA"
    assert response.json()["field"] == "policy_owner"


def test_a_non_string_list_member_is_refused(tmp_path):
    """Test 7: one bad chip fails the whole list, naming the list."""
    client, _ = _make_client(tmp_path)

    response = client.put(
        _metadata_url("open-finance-pd-2026", "bis-papers-168"),
        json={"legal_basis": ["FSA 2013", 7]},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_METADATA"
    assert response.json()["field"] == "legal_basis"


def test_blank_input_normalises_to_null(tmp_path):
    """Test 8: "cleared" and "never set" are one state on disk.

    A whitespace-only string and an empty list both mean the drafter left the
    field alone, and blank means "not set yet" — so both must store as `null`,
    or the panel would render a field as filled in with nothing in it.
    """
    client, workstreams_dir = _make_client(tmp_path)

    response = client.put(
        _metadata_url("open-finance-pd-2026", "bis-papers-168"),
        json={"policy_owner": "   ", "legal_basis": [], "applicability": ""},
    )

    assert response.status_code == 200
    metadata = response.json()["metadata"]
    assert metadata["policy_owner"] is None
    assert metadata["legal_basis"] is None
    assert metadata["applicability"] is None

    path = concepts_path(workstreams_dir, "open-finance-pd-2026", "bis-papers-168")
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["policy_owner"] is None
    assert saved["legal_basis"] is None


def test_an_over_long_field_is_refused(tmp_path):
    """Test 9: 2000 characters per scalar field, and past it nothing is written."""
    client, workstreams_dir = _make_client(tmp_path)
    path = concepts_path(workstreams_dir, "open-finance-pd-2026", "bis-papers-168")

    response = client.put(
        _metadata_url("open-finance-pd-2026", "bis-papers-168"),
        json={"applicability": "x" * 2001},
    )

    assert response.status_code == 413
    assert response.json()["code"] == "METADATA_TOO_LARGE"
    assert response.json()["field"] == "applicability"
    assert not path.exists()


def test_a_field_at_the_limit_is_accepted(tmp_path):
    """The cap is inclusive — 2000 characters is a valid clause quote, and only
    2001 is too many. Pins which side of the boundary rejects."""
    client, _ = _make_client(tmp_path)

    response = client.put(
        _metadata_url("open-finance-pd-2026", "bis-papers-168"),
        json={"applicability": "x" * 2000},
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["applicability"] == "x" * 2000


def test_too_many_list_members_are_refused(tmp_path):
    """Test 10: at most 50 chips."""
    client, workstreams_dir = _make_client(tmp_path)
    path = concepts_path(workstreams_dir, "open-finance-pd-2026", "bis-papers-168")

    response = client.put(
        _metadata_url("open-finance-pd-2026", "bis-papers-168"),
        json={"legal_basis": [f"Act {n}" for n in range(51)]},
    )

    assert response.status_code == 413
    assert response.json()["code"] == "METADATA_TOO_LARGE"
    assert response.json()["field"] == "legal_basis"
    assert not path.exists()


def test_an_over_long_list_member_is_refused(tmp_path):
    """The other half of the list cap: 50 members, each at most 200 characters."""
    client, _ = _make_client(tmp_path)

    response = client.put(
        _metadata_url("open-finance-pd-2026", "bis-papers-168"),
        json={"legal_basis": ["FSA 2013", "x" * 201]},
    )

    assert response.status_code == 413
    assert response.json()["code"] == "METADATA_TOO_LARGE"
    assert response.json()["field"] == "legal_basis"


def test_unknown_workstream_and_unknown_node_are_404_before_any_write(tmp_path):
    """Test 11: both ids are resolved against the graph before anything is written."""
    client, workstreams_dir = _make_client(tmp_path)
    before = sorted(p for p in workstreams_dir.rglob("*") if p.is_file())

    missing_ws = client.put(
        _metadata_url("nope", "x"), json={"policy_owner": "Aisyah R."}
    )
    assert missing_ws.status_code == 404
    assert missing_ws.json()["code"] == "WORKSTREAM_NOT_FOUND"

    missing_node = client.put(
        _metadata_url("open-finance-pd-2026", "nope"),
        json={"policy_owner": "Aisyah R."},
    )
    assert missing_node.status_code == 404
    assert missing_node.json()["code"] == "NODE_NOT_FOUND"

    assert sorted(p for p in workstreams_dir.rglob("*") if p.is_file()) == before


def test_a_traversal_shaped_node_id_writes_nothing_anywhere(tmp_path):
    """Test 12: a traversal-shaped node id never reaches the filesystem.

    `concepts_path` interpolates `node_id` straight into a path, so
    `../../escape` would write outside the workstream if it ever got as far as
    the write. Two layers stop it, and this pins both — asserting only the status
    code would not catch a write that happened before the refusal, so what is
    asserted is that no new file appeared anywhere under `tmp_path`.

    The percent-encoded form the spec names is refused by Starlette's router
    before the handler runs, so it carries the router's `{"detail": ...}` rather
    than a `_ws_error` body. That is a stricter outcome than the spec assumed,
    not a weaker one; the separator-shaped ids that DO reach the handler are
    covered below.
    """
    client, workstreams_dir = _make_client(tmp_path)
    before = sorted(p for p in tmp_path.rglob("*") if p.is_file())

    response = client.put(
        "/api/workstreams/open-finance-pd-2026/nodes/..%2F..%2Fescape/metadata",
        json={"policy_owner": "Aisyah R."},
    )

    assert response.status_code == 404
    assert sorted(p for p in tmp_path.rglob("*") if p.is_file()) == before
    assert not (tmp_path / "escape.json").exists()
    assert not (workstreams_dir.parent / "escape.json").exists()


def test_a_traversal_id_that_reaches_the_handler_is_node_not_found(tmp_path):
    """The other half of Test 12: the guard itself, not the router.

    A backslash-separated id routes as one path segment, so it lands in the
    handler with the separators intact — which is exactly the case the
    NODE_NOT_FOUND guard has to catch, and the reason it must precede the write
    rather than merely accompany it.
    """
    client, _ = _make_client(tmp_path)
    before = sorted(p for p in tmp_path.rglob("*") if p.is_file())

    response = client.put(
        "/api/workstreams/open-finance-pd-2026/nodes/..%5C..%5Cescape/metadata",
        json={"policy_owner": "Aisyah R."},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "NODE_NOT_FOUND"
    assert sorted(p for p in tmp_path.rglob("*") if p.is_file()) == before


def test_repeated_identical_saves_are_idempotent(tmp_path):
    """Test 13: the same payload twice yields a byte-identical file and the same 200."""
    client, workstreams_dir = _make_client(tmp_path)
    path = concepts_path(workstreams_dir, "open-finance-pd-2026", "bis-papers-168")
    payload = {
        "policy_owner": "Priya S.",
        "legal_basis": ["FSA 2013"],
    }

    first = client.put(
        _metadata_url("open-finance-pd-2026", "bis-papers-168"), json=payload
    )
    assert first.status_code == 200
    after_first = path.read_bytes()

    second = client.put(
        _metadata_url("open-finance-pd-2026", "bis-papers-168"), json=payload
    )
    assert second.status_code == 200
    assert path.read_bytes() == after_first
    assert second.json() == first.json()


def test_a_legacy_side_file_missing_the_newer_keys_is_upgraded_on_save(tmp_path):
    """Test 14: a side-file written before the last two fields existed still loads,
    and the first save through this route brings it up to all nine keys.

    No backfill migration: `load_concepts` returns the raw dict, so the missing
    keys read back as `None` and the panel renders them "Not set" — which is
    honest, because nobody ever recorded them.
    """
    client, workstreams_dir = _make_client(tmp_path)
    path = concepts_path(workstreams_dir, "open-finance-pd-2026", "bis-papers-168")
    path.parent.mkdir(parents=True, exist_ok=True)
    legacy = {
        "policy_owner": "Aisyah R.",
        "applicability": "Licensed banks.",
        "empowerment_framework": None,
        "issuance_date": None,
        "effective_date": None,
    }
    path.write_text(json.dumps(legacy, indent=2) + "\n", encoding="utf-8")

    before = client.get(
        "/api/workstreams/open-finance-pd-2026/nodes/bis-papers-168"
    ).json()["metadata"]
    assert before["status"] == "available"
    assert before["policy_owner"] == "Aisyah R."
    assert before.get("legal_basis") is None
    assert before.get("ismp_classification") is None

    response = client.put(
        _metadata_url("open-finance-pd-2026", "bis-papers-168"),
        json={
            "policy_owner": "Aisyah R.",
            "applicability": "Licensed banks.",
            "empowerment_framework": None,
            "issuance_date": None,
            "effective_date": None,
                "legal_basis": ["FSA 2013"],
            "ismp_classification": None,
        },
    )

    assert response.status_code == 200
    upgraded = json.loads(path.read_text(encoding="utf-8"))
    assert list(upgraded) == list(CONCEPT_FIELDS)
    assert upgraded["legal_basis"] == ["FSA 2013"]
    assert upgraded["ismp_classification"] is None


def test_a_body_that_is_not_an_object_is_refused(tmp_path):
    """A JSON array or bare string is not a profile. Named separately from the
    field-level type checks because there is no field to blame."""
    client, _ = _make_client(tmp_path)

    for body in (["policy_owner"], "policy_owner", 7):
        response = client.put(
            _metadata_url("open-finance-pd-2026", "bis-papers-168"), json=body
        )
        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_METADATA"
        assert "field" not in response.json()


def test_a_bare_string_list_field_is_stored_as_is(tmp_path):
    """`legal_basis` tolerates a scalar, because older side-files
    carry one and the panel's `asList` already renders either shape. Nothing
    splits it on commas — that is the form's job, not the route's."""
    client, _ = _make_client(tmp_path)

    response = client.put(
        _metadata_url("open-finance-pd-2026", "bis-papers-168"),
        json={"legal_basis": "FSA 2013, IFSA 2013"},
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["legal_basis"] == "FSA 2013, IFSA 2013"


# --- ISMP classification is a closed vocabulary -----------------------------
# The four BNM security classifications. Free text was wrong here: these are
# handling categories with real consequences, not a label to invent.


@pytest.mark.parametrize("value", concepts.ISMP_CLASSIFICATIONS)
def test_each_ismp_classification_is_accepted(value: str, tmp_path):
    client, _ = _make_client(tmp_path)

    response = client.put(
        _metadata_url("open-finance-pd-2026", "bis-papers-168"),
        json={"ismp_classification": value},
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["ismp_classification"] == value


def test_an_ismp_classification_outside_the_four_is_refused(tmp_path):
    """The old free-text values ("Prudential") are exactly what this refuses."""
    client, workstreams_dir = _make_client(tmp_path)
    path = concepts_path(workstreams_dir, "open-finance-pd-2026", "bis-papers-168")

    response = client.put(
        _metadata_url("open-finance-pd-2026", "bis-papers-168"),
        json={"ismp_classification": "Prudential"},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_ISMP_CLASSIFICATION"
    assert response.json()["field"] == "ismp_classification"
    assert not path.exists(), "a refused save must not write"


def test_an_unset_ismp_classification_stays_legal(tmp_path):
    """Unset is the honest state for a document nobody has classified — the
    panel renders it as pending rather than guessing."""
    client, _ = _make_client(tmp_path)

    response = client.put(
        _metadata_url("open-finance-pd-2026", "bis-papers-168"),
        json={"policy_owner": "Priya S.", "ismp_classification": None},
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["ismp_classification"] is None


def test_the_removed_fields_are_now_unknown(tmp_path):
    """`keywords` and `requirement` left the profile on 30 Jul 2026. A client
    still sending either is told, rather than having the value silently dropped."""
    client, _ = _make_client(tmp_path)

    for field in ("keywords", "requirement"):
        response = client.put(
            _metadata_url("open-finance-pd-2026", "bis-papers-168"),
            json={field: "anything"},
        )
        assert response.status_code == 400
        assert response.json()["code"] == "UNKNOWN_METADATA_FIELD"
        assert response.json()["field"] == field
