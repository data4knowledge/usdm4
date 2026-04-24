"""Tests for RuleDDF00244 — NarrativeContentItem.text <usdm:ref> validation."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00244 import (
    RuleDDF00244,
    _check_ref,
    _parse_ref,
)
from usdm4.rules.rule_template import RuleTemplate


def test_parse_ref_all_attrs():
    out = _parse_ref(' klass="X" id="x1" attribute="name"')
    assert out == {"klass": "X", "id": "x1", "attribute": "name"}


def test_check_ref_missing_fields():
    msg = _check_ref(MagicMock(), {"klass": "X"})
    assert "missing" in msg


def test_check_ref_unresolved():
    data = MagicMock()
    data.instance_by_id.return_value = None
    msg = _check_ref(data, {"klass": "X", "id": "g", "attribute": "name"})
    assert "does not resolve" in msg


def test_check_ref_wrong_klass():
    data = MagicMock()
    data.instance_by_id.return_value = {"id": "i", "instanceType": "Y"}
    msg = _check_ref(data, {"klass": "X", "id": "i", "attribute": "name"})
    assert "expected X" in msg


def test_check_ref_missing_attribute():
    data = MagicMock()
    data.instance_by_id.return_value = {"id": "i", "instanceType": "X"}
    msg = _check_ref(data, {"klass": "X", "id": "i", "attribute": "name"})
    assert "not present" in msg


def test_check_ref_ok():
    data = MagicMock()
    data.instance_by_id.return_value = {"id": "i", "instanceType": "X", "name": "v"}
    assert _check_ref(data, {"klass": "X", "id": "i", "attribute": "name"}) is None


class TestRuleDDF00244:
    def test_metadata(self):
        rule = RuleDDF00244()
        assert rule._rule == "DDF00244"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items, id_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        data.instance_by_id.side_effect = lambda tid: (id_map or {}).get(tid)
        return data

    def test_non_string_text_skipped(self):
        rule = RuleDDF00244()
        data = self._data([{"id": "N1", "text": None}])
        assert rule.validate({"data": data}) is True

    def test_text_without_marker_skipped(self):
        rule = RuleDDF00244()
        data = self._data([{"id": "N1", "text": "plain text"}])
        assert rule.validate({"data": data}) is True

    def test_resolved_ref_passes(self):
        rule = RuleDDF00244()
        data = self._data(
            [
                {
                    "id": "N1",
                    "text": 'see <usdm:ref klass="X" id="x1" attribute="name"/>',
                }
            ],
            id_map={"x1": {"id": "x1", "instanceType": "X", "name": "v"}},
        )
        assert rule.validate({"data": data}) is True

    def test_unresolved_ref_fails(self):
        rule = RuleDDF00244()
        data = self._data(
            [
                {
                    "id": "N1",
                    "text": 'see <usdm:ref klass="X" id="ghost" attribute="name"/>',
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
