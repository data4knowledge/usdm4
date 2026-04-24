"""Tests for RuleDDF00124 — ParameterMap <usdm:ref> must resolve in data."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00124 import RuleDDF00124, _check_ref, _parse_ref
from usdm4.rules.rule_template import RuleTemplate


# ---------------------------------------------------------------------------
# _parse_ref helper
# ---------------------------------------------------------------------------


def test_parse_ref_extracts_all_three():
    out = _parse_ref(' klass="X" id="x1" attribute="name"')
    assert out == {"klass": "X", "id": "x1", "attribute": "name"}


def test_parse_ref_with_missing_attrs_returns_subset():
    out = _parse_ref(' klass="X"')
    assert out == {"klass": "X"}


# ---------------------------------------------------------------------------
# _check_ref helper
# ---------------------------------------------------------------------------


def test_check_ref_missing_fields_returns_message():
    data = MagicMock()
    msg = _check_ref(data, {"klass": "X"})
    assert "missing" in msg


def test_check_ref_unresolved_id():
    data = MagicMock()
    data.instance_by_id.return_value = None
    msg = _check_ref(data, {"klass": "X", "id": "ghost", "attribute": "name"})
    assert "does not resolve" in msg


def test_check_ref_wrong_klass():
    data = MagicMock()
    data.instance_by_id.return_value = {"id": "i1", "instanceType": "Y"}
    msg = _check_ref(data, {"klass": "X", "id": "i1", "attribute": "name"})
    assert "expected X" in msg


def test_check_ref_missing_attribute():
    data = MagicMock()
    data.instance_by_id.return_value = {"id": "i1", "instanceType": "X"}
    msg = _check_ref(data, {"klass": "X", "id": "i1", "attribute": "name"})
    assert "not present" in msg


def test_check_ref_happy_returns_none():
    data = MagicMock()
    data.instance_by_id.return_value = {"id": "i1", "instanceType": "X", "name": "ok"}
    assert _check_ref(data, {"klass": "X", "id": "i1", "attribute": "name"}) is None


# ---------------------------------------------------------------------------
# Rule validate()
# ---------------------------------------------------------------------------


class TestRuleDDF00124:
    def test_metadata(self):
        rule = RuleDDF00124()
        assert rule._rule == "DDF00124"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, pms, id_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = pms
        data.path_by_id.return_value = "$.path"
        data.instance_by_id.side_effect = lambda tid: (id_map or {}).get(tid)
        return data

    def test_non_string_reference_skipped(self):
        rule = RuleDDF00124()
        data = self._data([{"id": "P1", "reference": None}])
        assert rule.validate({"data": data}) is True

    def test_resolved_reference_passes(self):
        rule = RuleDDF00124()
        data = self._data(
            [
                {
                    "id": "P1",
                    "reference": 'uses <usdm:ref klass="X" id="x1" attribute="name"/>',
                }
            ],
            id_map={"x1": {"id": "x1", "instanceType": "X", "name": "val"}},
        )
        assert rule.validate({"data": data}) is True

    def test_unresolved_reference_fails(self):
        rule = RuleDDF00124()
        data = self._data(
            [
                {
                    "id": "P1",
                    "reference": 'sees <usdm:ref klass="X" id="ghost" attribute="name"/>',
                }
            ],
            id_map={},
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
