"""Tests for RuleDDF00246 — <usdm:tag> names must be in Dictionary parameterMaps."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00246 import RuleDDF00246
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00246:
    def test_metadata(self):
        rule = RuleDDF00246()
        assert rule._rule == "DDF00246"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, by_klass, id_map=None):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: by_klass.get(k, [])
        data.path_by_id.return_value = "$.path"
        data.instance_by_id.side_effect = lambda tid: (id_map or {}).get(tid)
        return data

    def test_text_without_tag_is_skipped(self):
        rule = RuleDDF00246()
        data = self._data({"Objective": [{"id": "O1", "text": "plain"}]})
        assert rule.validate({"data": data}) is True

    def test_non_string_text_is_skipped(self):
        rule = RuleDDF00246()
        data = self._data({"Objective": [{"id": "O1", "text": None}]})
        assert rule.validate({"data": data}) is True

    def test_tag_without_dictionary_id_fails(self):
        rule = RuleDDF00246()
        data = self._data(
            {"Objective": [{"id": "O1", "text": 'see <usdm:tag name="foo"/>'}]}
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_dictionary_id_doesnt_resolve_fails(self):
        rule = RuleDDF00246()
        data = self._data(
            {
                "Objective": [
                    {
                        "id": "O1",
                        "text": 'see <usdm:tag name="foo"/>',
                        "dictionaryId": "D1",
                    }
                ]
            },
            id_map={},  # D1 doesn't exist
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_tag_name_not_in_parameter_maps_fails(self):
        rule = RuleDDF00246()
        data = self._data(
            {
                "Objective": [
                    {
                        "id": "O1",
                        "text": 'see <usdm:tag name="missing"/>',
                        "dictionaryId": "D1",
                    }
                ]
            },
            id_map={
                "D1": {
                    "id": "D1",
                    "parameterMaps": [{"tag": "other"}, None, {"tag": None}],
                }
            },
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_tag_in_parameter_maps_passes(self):
        rule = RuleDDF00246()
        data = self._data(
            {
                "Objective": [
                    {
                        "id": "O1",
                        "text": 'see <usdm:tag name="foo"/>',
                        "dictionaryId": "D1",
                    }
                ]
            },
            id_map={"D1": {"id": "D1", "parameterMaps": [{"tag": "foo"}]}},
        )
        assert rule.validate({"data": data}) is True

    def test_tag_regex_no_match_skips(self):
        """`<usdm:tag` appears but not in the valid form — findall returns nothing."""
        rule = RuleDDF00246()
        data = self._data(
            {
                "Objective": [
                    {"id": "O1", "text": "fragment <usdm:tag with no name attr"}
                ]
            }
        )
        # `<usdm:tag` is in text → enters loop, but regex finds no names,
        # so tag_names is empty → continues without failure.
        assert rule.validate({"data": data}) is True
