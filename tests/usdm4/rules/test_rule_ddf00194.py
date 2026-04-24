"""Tests for RuleDDF00194 — Address must have at least one attribute specified."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00194 import RuleDDF00194
from usdm4.rules.rule_template import RuleTemplate


def _data(addresses):
    data = MagicMock()
    data.instances_by_klass.side_effect = lambda k: (
        addresses if k == "Address" else []
    )
    data.path_by_id.return_value = "$.path"
    return data


class TestRuleDDF00194:
    def test_metadata(self):
        rule = RuleDDF00194()
        assert rule._rule == "DDF00194"
        assert rule._level == RuleTemplate.ERROR

    def test_iterates_Address_not_LegalAddress(self):
        """Regression: earlier impl iterated LegalAddress (not in V4 API);
        loop never ran and real 'all blank' cases slipped through."""
        rule = RuleDDF00194()
        blank = {"id": "A1"}  # no attrs at all
        data = MagicMock()

        def by_klass(k):
            if k == "LegalAddress":
                return [blank]  # if rule iterates this, it'll miss the real class
            if k == "Address":
                return [blank]
            return []

        data.instances_by_klass.side_effect = by_klass
        data.path_by_id.return_value = "$.path"
        assert rule.validate({"data": data}) is False

    def test_all_attributes_blank_fails(self):
        rule = RuleDDF00194()
        data = _data([{"id": "A1"}])
        assert rule.validate({"data": data}) is False
        assert "at least one" in rule.errors().dump()

    def test_text_only_passes(self):
        rule = RuleDDF00194()
        data = _data([{"id": "A1", "text": "100 Main St"}])
        assert rule.validate({"data": data}) is True

    def test_lines_only_passes(self):
        rule = RuleDDF00194()
        data = _data([{"id": "A1", "lines": ["100 Main St"]}])
        assert rule.validate({"data": data}) is True

    def test_empty_lines_list_treated_as_blank(self):
        rule = RuleDDF00194()
        data = _data([{"id": "A1", "lines": []}])
        assert rule.validate({"data": data}) is False

    def test_country_code_object_counts_as_specified(self):
        rule = RuleDDF00194()
        data = _data([{"id": "A1", "country": {"code": "US"}}])
        assert rule.validate({"data": data}) is True

    def test_empty_country_object_treated_as_blank(self):
        rule = RuleDDF00194()
        data = _data([{"id": "A1", "country": {}}])
        assert rule.validate({"data": data}) is False

    def test_empty_strings_treated_as_blank(self):
        rule = RuleDDF00194()
        # All present but empty strings — still blank per the rule
        data = _data(
            [
                {
                    "id": "A1",
                    "text": "",
                    "city": "",
                    "district": "",
                    "state": "",
                    "postalCode": "",
                }
            ]
        )
        assert rule.validate({"data": data}) is False

    def test_multiple_addresses_accumulate(self):
        rule = RuleDDF00194()
        data = _data([{"id": "A1"}, {"id": "A2", "city": "Paris"}, {"id": "A3"}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2
