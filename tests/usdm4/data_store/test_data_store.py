"""Direct tests for DataStore, DataStoreErrorLocation, and DecompositionError.

Exercises the load/decompose happy path and every error branch with
small, hand-built JSON documents written to a tmp_path.
"""

import json

import pytest

from src.usdm4.data_store.data_store import (
    DataStore,
    DataStoreErrorLocation,
    DecompositionError,
)


# ---------------------------------------------------------------------------
# DataStoreErrorLocation
# ---------------------------------------------------------------------------


def test_error_location_to_dict_and_str():
    loc = DataStoreErrorLocation("$.a", "Klass", "attr")
    assert loc.to_dict() == {"path": "$.a", "klass": "Klass", "attribute": "attr"}
    # __str__ includes all three fields
    s = str(loc)
    assert "Klass" in s
    assert "attr" in s
    assert "$.a" in s


# ---------------------------------------------------------------------------
# DecompositionError
# ---------------------------------------------------------------------------


def test_decomposition_error_str_includes_message():
    loc = DataStoreErrorLocation("$", "Study", "id")
    err = DecompositionError(loc, "missing id attribute")
    assert "missing id attribute" in str(err)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write(tmp_path, payload):
    p = tmp_path / "study.json"
    p.write_text(json.dumps(payload))
    return str(p)


def _valid_study_payload():
    """Minimal decomposable study doc with a handful of nested instances."""
    return {
        "study": {
            "id": "S1",
            "instanceType": "Study",
            "versions": [
                {"id": "V1", "instanceType": "StudyVersion"},
                {"id": "V2", "instanceType": "StudyVersion"},
            ],
            "sponsor": {"id": "SP1", "instanceType": "Sponsor"},
        }
    }


# ---------------------------------------------------------------------------
# Happy path — decompose builds all four indexes
# ---------------------------------------------------------------------------


def test_decompose_builds_indexes(tmp_path):
    path = _write(tmp_path, _valid_study_payload())
    ds = DataStore(path)
    ds.decompose()

    # Instance lookup by id
    assert ds.instance_by_id("V1")["id"] == "V1"
    assert ds.instance_by_id("SP1")["id"] == "SP1"
    assert ds.instance_by_id("unknown") is None

    # Instances by klass
    versions = ds.instances_by_klass("StudyVersion")
    assert len(versions) == 2
    assert ds.instances_by_klass("not-a-klass") == []

    # path_by_id
    assert ds.path_by_id("V1") is not None
    assert ds.path_by_id("unknown") is None


def test_decompose_null_study_id_rewritten(tmp_path):
    payload = _valid_study_payload()
    payload["study"]["id"] = None
    path = _write(tmp_path, payload)
    ds = DataStore(path)
    ds.decompose()
    assert ds.data["study"]["id"] == "$root.study.id"


# ---------------------------------------------------------------------------
# parent_by_klass — walks the parent chain
# ---------------------------------------------------------------------------


def test_parent_by_klass_finds_ancestor(tmp_path):
    path = _write(tmp_path, _valid_study_payload())
    ds = DataStore(path)
    ds.decompose()

    # V1's parent chain contains Study
    parent = ds.parent_by_klass("V1", "Study")
    assert parent is not None
    assert parent["instanceType"] == "Study"

    # List form also works
    parent2 = ds.parent_by_klass("V1", ["Study"])
    assert parent2 is parent


def test_parent_by_klass_returns_none_for_unknown_id(tmp_path):
    path = _write(tmp_path, _valid_study_payload())
    ds = DataStore(path)
    ds.decompose()
    assert ds.parent_by_klass("missing", "Study") is None


def test_parent_by_klass_returns_none_when_no_match(tmp_path):
    """Walks to the top-level Wrapper (no instanceType) -> returns None."""
    path = _write(tmp_path, _valid_study_payload())
    ds = DataStore(path)
    ds.decompose()
    assert ds.parent_by_klass("V1", "NoSuchKlass") is None


# ---------------------------------------------------------------------------
# decompose — error branches
# ---------------------------------------------------------------------------


def test_decompose_missing_study_raises(tmp_path):
    path = _write(tmp_path, {"notstudy": {}})
    ds = DataStore(path)
    with pytest.raises(DecompositionError) as ex:
        ds.decompose()
    assert "missing study attribute" in str(ex.value)


def test_decompose_missing_study_id_raises(tmp_path):
    path = _write(tmp_path, {"study": {"instanceType": "Study"}})
    ds = DataStore(path)
    with pytest.raises(DecompositionError) as ex:
        ds.decompose()
    assert "missing id attribute" in str(ex.value)


def test_decompose_child_missing_id_raises(tmp_path):
    payload = {
        "study": {
            "id": "S1",
            "instanceType": "Study",
            "versions": [
                {"instanceType": "StudyVersion"}  # no id
            ],
        }
    }
    path = _write(tmp_path, payload)
    ds = DataStore(path)
    with pytest.raises(DecompositionError) as ex:
        ds.decompose()
    assert "missing id attribute" in str(ex.value)


def test_decompose_child_missing_instance_type_raises(tmp_path):
    payload = {
        "study": {
            "id": "S1",
            "instanceType": "Study",
            "versions": [
                {"id": "V1"}  # no instanceType
            ],
        }
    }
    path = _write(tmp_path, payload)
    ds = DataStore(path)
    with pytest.raises(DecompositionError) as ex:
        ds.decompose()
    assert "missing instanceType attribute" in str(ex.value)


def test_decompose_records_duplicate_id(tmp_path):
    payload = {
        "study": {
            "id": "S1",
            "instanceType": "Study",
            "versions": [
                {"id": "V1", "instanceType": "StudyVersion"},
                {"id": "V1", "instanceType": "StudyVersion"},  # duplicate
            ],
        }
    }
    path = _write(tmp_path, payload)
    ds = DataStore(path)
    ds.decompose()
    # Should report duplicate id; store still constructed
    assert ds.errors.count() >= 1
