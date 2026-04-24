"""Tests for RuleDDF00040 — each StudyElement must be referenced by at least one StudyCell."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00040 import RuleDDF00040
from usdm4.rules.rule_template import RuleTemplate


def _data(elements=None, cells=None):
    data = MagicMock()
    data.instances_by_klass.side_effect = lambda k: {
        "StudyElement": elements or [],
        "StudyCell": cells or [],
    }.get(k, [])
    data.path_by_id.return_value = "$.path"
    return data


class TestRuleDDF00040:
    def test_metadata(self):
        rule = RuleDDF00040()
        assert rule._rule == "DDF00040"
        assert rule._level == RuleTemplate.ERROR

    def test_all_elements_referenced_passes(self):
        rule = RuleDDF00040()
        data = _data(
            elements=[{"id": "E1"}, {"id": "E2"}],
            cells=[{"id": "C1", "elementIds": ["E1", "E2"]}],
        )
        assert rule.validate({"data": data}) is True

    def test_element_referenced_by_any_cell_passes(self):
        rule = RuleDDF00040()
        data = _data(
            elements=[{"id": "E1"}, {"id": "E2"}],
            cells=[
                {"id": "C1", "elementIds": ["E1"]},
                {"id": "C2", "elementIds": ["E2"]},
            ],
        )
        assert rule.validate({"data": data}) is True

    def test_orphan_element_fails(self):
        rule = RuleDDF00040()
        data = _data(
            elements=[{"id": "E1"}, {"id": "E2"}],
            cells=[{"id": "C1", "elementIds": ["E1"]}],
        )
        assert rule.validate({"data": data}) is False
        assert "E2" in rule.errors().dump()
        assert rule.errors().count() == 1

    def test_no_cells_flags_every_element(self):
        rule = RuleDDF00040()
        data = _data(elements=[{"id": "E1"}, {"id": "E2"}], cells=[])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2

    def test_no_elements_passes_vacuously(self):
        rule = RuleDDF00040()
        data = _data(elements=[], cells=[{"id": "C1", "elementIds": ["E1"]}])
        assert rule.validate({"data": data}) is True

    def test_non_string_element_ids_ignored(self):
        rule = RuleDDF00040()
        data = _data(
            elements=[{"id": "E1"}],
            cells=[{"id": "C1", "elementIds": [None, "", "E1"]}],
        )
        assert rule.validate({"data": data}) is True
