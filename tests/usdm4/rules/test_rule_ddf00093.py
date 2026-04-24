"""Tests for RuleDDF00093 — StudyVersion dateValues uniqueness by (type, scopes)."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00093 import RuleDDF00093, _date_key
from usdm4.rules.rule_template import RuleTemplate


# ---------------------------------------------------------------------------
# _date_key helper
# ---------------------------------------------------------------------------


def test_date_key_type_missing_is_none():
    key = _date_key({})
    assert key == (None, frozenset())


def test_date_key_type_not_dict_is_none():
    key = _date_key({"type": "not-a-dict"})
    assert key == (None, frozenset())


def test_date_key_extracts_type_code():
    key = _date_key({"type": {"code": "C1"}})
    assert key == ("C1", frozenset())


def test_date_key_scope_order_is_irrelevant():
    """`frozenset` ensures scope order doesn't matter."""
    a = _date_key(
        {
            "type": {"code": "C1"},
            "geographicScopes": [{"type": {"code": "G"}}, {"type": {"code": "US"}}],
        }
    )
    b = _date_key(
        {
            "type": {"code": "C1"},
            "geographicScopes": [{"type": {"code": "US"}}, {"type": {"code": "G"}}],
        }
    )
    assert a == b


def test_date_key_filters_non_dict_scopes():
    key = _date_key(
        {
            "type": {"code": "C1"},
            "geographicScopes": [
                {"type": {"code": "G"}},
                None,
                "bogus",
                {"type": "not-a-dict"},
            ],
        }
    )
    # Only the valid {"type": {"code": "G"}} entry contributes.
    assert key == ("C1", frozenset({"G"}))


# ---------------------------------------------------------------------------
# Rule validate()
# ---------------------------------------------------------------------------


class TestRuleDDF00093:
    def test_metadata(self):
        rule = RuleDDF00093()
        assert rule._rule == "DDF00093"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, versions):
        data = MagicMock()
        data.instances_by_klass.return_value = versions
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_date_values_passes(self):
        rule = RuleDDF00093()
        data = self._data([{"id": "SV1"}])
        assert rule.validate({"data": data}) is True

    def test_non_dict_date_skipped(self):
        rule = RuleDDF00093()
        data = self._data([{"id": "SV1", "dateValues": ["bogus", None]}])
        assert rule.validate({"data": data}) is True

    def test_missing_type_skipped(self):
        """Dates without a type.code (key[0] is None) are skipped entirely."""
        rule = RuleDDF00093()
        data = self._data([{"id": "SV1", "dateValues": [{"id": "D1"}, {"id": "D2"}]}])
        assert rule.validate({"data": data}) is True

    def test_unique_dates_pass(self):
        rule = RuleDDF00093()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "dateValues": [
                        {"id": "D1", "type": {"code": "C1"}},
                        {"id": "D2", "type": {"code": "C2"}},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_dates_fail_with_one_error_per_date(self):
        """Two dates with the same (type, scopes) key → two failures."""
        rule = RuleDDF00093()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "dateValues": [
                        {
                            "id": "D1",
                            "type": {"code": "C1"},
                            "geographicScopes": [{"type": {"code": "G"}}],
                        },
                        {
                            "id": "D2",
                            "type": {"code": "C1"},
                            "geographicScopes": [{"type": {"code": "G"}}],
                        },
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2

    def test_different_scopes_dont_collide(self):
        rule = RuleDDF00093()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "dateValues": [
                        {
                            "id": "D1",
                            "type": {"code": "C1"},
                            "geographicScopes": [{"type": {"code": "G"}}],
                        },
                        {
                            "id": "D2",
                            "type": {"code": "C1"},
                            "geographicScopes": [{"type": {"code": "US"}}],
                        },
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True
