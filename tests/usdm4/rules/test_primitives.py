"""Tests for the rule body primitives (src/usdm4/rules/primitives.py).

All functions are pure data helpers; the data_store dependency in
``any_ids_unresolved``, ``same_scope`` and ``scope_of`` is satisfied
with MagicMock.
"""

from unittest.mock import MagicMock

from src.usdm4.rules.primitives import (
    any_ids_unresolved,
    children,
    duplicate_values,
    duplicates_by,
    not_in_set,
    same_scope,
    scope_of,
)


# ---------------------------------------------------------------------------
# children
# ---------------------------------------------------------------------------


def test_children_returns_list_when_present():
    assert children({"items": [1, 2]}, "items") == [1, 2]


def test_children_handles_missing_attr():
    assert children({}, "items") == []


def test_children_handles_none_value():
    assert children({"items": None}, "items") == []


# ---------------------------------------------------------------------------
# duplicates_by
# ---------------------------------------------------------------------------


def test_duplicates_by_returns_only_duplicated_groups():
    items = [
        {"name": "A"},
        {"name": "B"},
        {"name": "A"},  # dupe of first
        {"name": "C"},
    ]
    result = duplicates_by(items, lambda x: x["name"])
    assert len(result) == 2
    assert all(it["name"] == "A" for it in result)


def test_duplicates_by_ignores_none_and_empty_keys():
    items = [
        {"name": None},
        {"name": None},
        {"name": ""},
        {"name": ""},
        {"name": "X"},
    ]
    assert duplicates_by(items, lambda x: x["name"]) == []


def test_duplicates_by_empty_input():
    assert duplicates_by([], lambda x: x["name"]) == []


# ---------------------------------------------------------------------------
# duplicate_values
# ---------------------------------------------------------------------------


def test_duplicate_values_returns_values_seen_more_than_once():
    assert duplicate_values(["a", "b", "a", "c", "b", "b"]) == ["a", "b"]


def test_duplicate_values_no_duplicates():
    assert duplicate_values(["a", "b", "c"]) == []


def test_duplicate_values_empty_and_none():
    assert duplicate_values([]) == []
    assert duplicate_values(None) == []


# ---------------------------------------------------------------------------
# not_in_set
# ---------------------------------------------------------------------------


def test_not_in_set_true_when_absent():
    assert not_in_set("x", ["a", "b", "c"]) is True


def test_not_in_set_false_when_present():
    assert not_in_set("b", ["a", "b", "c"]) is False


def test_not_in_set_handles_none_allowed():
    assert not_in_set("x", None) is True


# ---------------------------------------------------------------------------
# any_ids_unresolved
# ---------------------------------------------------------------------------


def test_any_ids_unresolved_returns_missing_ids():
    ds = MagicMock()
    ds.instance_by_id.side_effect = lambda i: {"id": i} if i == "ok" else None
    result = any_ids_unresolved(["ok", "missing1", "missing2"], ds)
    assert result == ["missing1", "missing2"]


def test_any_ids_unresolved_empty_or_none():
    ds = MagicMock()
    assert any_ids_unresolved([], ds) == []
    assert any_ids_unresolved(None, ds) == []


def test_any_ids_unresolved_all_resolved():
    ds = MagicMock()
    ds.instance_by_id.return_value = {"id": "x"}
    assert any_ids_unresolved(["a", "b"], ds) == []


# ---------------------------------------------------------------------------
# same_scope
# ---------------------------------------------------------------------------


def test_same_scope_true_when_parents_match():
    ds = MagicMock()
    ds.parent_by_klass.side_effect = [{"id": "SP"}, {"id": "SP"}]
    assert same_scope(ds, "a", "b", ["StudyProtocol"]) is True


def test_same_scope_false_when_parents_differ():
    ds = MagicMock()
    ds.parent_by_klass.side_effect = [{"id": "SP1"}, {"id": "SP2"}]
    assert same_scope(ds, "a", "b", ["StudyProtocol"]) is False


def test_same_scope_none_when_first_parent_missing():
    ds = MagicMock()
    ds.parent_by_klass.side_effect = [None, {"id": "SP"}]
    assert same_scope(ds, "a", "b", ["StudyProtocol"]) is None


def test_same_scope_none_when_second_parent_missing():
    ds = MagicMock()
    ds.parent_by_klass.side_effect = [{"id": "SP"}, None]
    assert same_scope(ds, "a", "b", ["StudyProtocol"]) is None


# ---------------------------------------------------------------------------
# scope_of
# ---------------------------------------------------------------------------


def test_scope_of_delegates_to_data_store():
    ds = MagicMock()
    ds.parent_by_klass.return_value = {"id": "SP"}
    result = scope_of(ds, "a", ["StudyProtocol"])
    assert result == {"id": "SP"}
    ds.parent_by_klass.assert_called_once_with("a", ["StudyProtocol"])
