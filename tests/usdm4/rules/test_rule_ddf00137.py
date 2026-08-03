"""Tests for RuleDDF00137 — ParameterMap.reference <usdm:ref> format."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00137 import RuleDDF00137, _find_malformed
from usdm4.rules.rule_template import RuleTemplate


# ---------------------------------------------------------------------------
# _find_malformed helper
# ---------------------------------------------------------------------------


def test_find_malformed_no_ref_yields_nothing():
    assert list(_find_malformed("plain text with no ref")) == []


def test_find_malformed_unterminated_opener():
    """`<usdm:ref` without a closing `>` is a fatal case — reason logged and
    the generator exits (return on line 35)."""
    out = list(_find_malformed('prefix <usdm:ref klass="X" '))
    assert len(out) == 1
    _, reason = out[0]
    assert "not closed" in reason


def test_find_malformed_not_self_closing_and_no_paired_closing():
    """Tag closes with `>` but no `/>` and no `</usdm:ref>` follows."""
    out = list(_find_malformed('<usdm:ref klass="X" id="x1" attribute="a"> tail'))
    assert len(out) == 1
    _, reason = out[0]
    assert "does not end with" in reason


def test_find_malformed_missing_attributes():
    """Well-formed self-closing tag but missing `id` and `attribute`."""
    out = list(_find_malformed('<usdm:ref klass="X"/>'))
    assert len(out) == 1
    _, reason = out[0]
    assert "missing or malformed attribute" in reason
    assert "id" in reason
    assert "attribute" in reason


def test_find_malformed_valid_self_closing_is_accepted():
    out = list(_find_malformed('<usdm:ref klass="X" id="x1" attribute="name"/>'))
    assert out == []


def test_find_malformed_valid_paired_closing_is_accepted():
    out = list(
        _find_malformed('<usdm:ref klass="X" id="x1" attribute="name"></usdm:ref>')
    )
    assert out == []


# ---------------------------------------------------------------------------
# Rule validate()
# ---------------------------------------------------------------------------


class TestRuleDDF00137:
    def test_metadata(self):
        rule = RuleDDF00137()
        assert rule._rule == "DDF00137"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, pms):
        data = MagicMock()
        data.instances_by_klass.return_value = pms
        data.path_by_id.return_value = "$.path"
        return data

    def test_non_string_reference_is_skipped(self):
        rule = RuleDDF00137()
        data = self._data([{"id": "P1", "reference": None}])
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_reference_without_ref_tag_is_skipped(self):
        rule = RuleDDF00137()
        data = self._data([{"id": "P1", "reference": "5 mg"}])
        assert rule.validate({"data": data}) is True

    def test_malformed_reference_logs_failure(self):
        rule = RuleDDF00137()
        data = self._data(
            [{"id": "P1", "reference": '<usdm:ref klass="X"/>'}]  # missing attrs
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_valid_reference_passes(self):
        rule = RuleDDF00137()
        data = self._data(
            [
                {
                    "id": "P1",
                    "reference": '<usdm:ref klass="X" id="x1" attribute="name"/>',
                }
            ]
        )
        assert rule.validate({"data": data}) is True
