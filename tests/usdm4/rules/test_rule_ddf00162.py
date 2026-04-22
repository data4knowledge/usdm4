"""Tests for RuleDDF00162 — NarrativeContentItem.text <usdm:ref> format."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00162 import RuleDDF00162, _find_malformed
from usdm4.rules.rule_template import RuleTemplate


# ---------------------------------------------------------------------------
# _find_malformed helper
# ---------------------------------------------------------------------------


def test_find_malformed_no_ref_yields_nothing():
    assert list(_find_malformed("no refs here")) == []


def test_find_malformed_unterminated_opener():
    """`<usdm:ref` without a closing `>` — returns immediately after yielding."""
    out = list(_find_malformed('<usdm:ref klass="X" '))
    assert len(out) == 1
    assert "not closed" in out[0][1]


def test_find_malformed_not_self_closing_and_no_paired_closing():
    out = list(_find_malformed('<usdm:ref klass="X" id="x1" attribute="a"> tail'))
    assert len(out) == 1
    assert "does not end with" in out[0][1]


def test_find_malformed_missing_attributes():
    out = list(_find_malformed('<usdm:ref klass="X"/>'))
    assert len(out) == 1
    assert "missing or malformed attribute" in out[0][1]


def test_find_malformed_valid_self_closing_is_accepted():
    assert list(_find_malformed('<usdm:ref klass="X" id="x1" attribute="name"/>')) == []


def test_find_malformed_valid_paired_closing_is_accepted():
    assert (
        list(
            _find_malformed('<usdm:ref klass="X" id="x1" attribute="name"></usdm:ref>')
        )
        == []
    )


# ---------------------------------------------------------------------------
# Rule validate()
# ---------------------------------------------------------------------------


class TestRuleDDF00162:
    def test_metadata(self):
        rule = RuleDDF00162()
        assert rule._rule == "DDF00162"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_non_string_text_is_skipped(self):
        rule = RuleDDF00162()
        data = self._data([{"id": "N1", "text": None}])
        assert rule.validate({"data": data}) is True

    def test_text_without_ref_tag_is_skipped(self):
        rule = RuleDDF00162()
        data = self._data([{"id": "N1", "text": "Lorem ipsum dolor"}])
        assert rule.validate({"data": data}) is True

    def test_malformed_text_logs_failure(self):
        rule = RuleDDF00162()
        data = self._data([{"id": "N1", "text": 'before <usdm:ref klass="X"/> after'}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_valid_text_passes(self):
        rule = RuleDDF00162()
        data = self._data(
            [
                {
                    "id": "N1",
                    "text": 'See <usdm:ref klass="X" id="x1" attribute="name"/>',
                }
            ]
        )
        assert rule.validate({"data": data}) is True
