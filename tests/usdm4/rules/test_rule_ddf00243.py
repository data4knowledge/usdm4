"""Tests for RuleDDF00243 — StudyArm × StudyEpoch grid coverage by StudyCells."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00243 import RuleDDF00243
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00243:
    def test_metadata(self):
        rule = RuleDDF00243()
        assert rule._rule == "DDF00243"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, designs_by_klass):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: designs_by_klass.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_arms_or_no_epochs_is_skipped(self):
        rule = RuleDDF00243()
        design = {"id": "D1", "arms": [], "epochs": [{"id": "E1"}], "studyCells": []}
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_full_grid_passes(self):
        rule = RuleDDF00243()
        design = {
            "id": "D1",
            "arms": [{"id": "A1"}, {"id": "A2"}],
            "epochs": [{"id": "E1"}, {"id": "E2"}],
            "studyCells": [
                {"armId": "A1", "epochId": "E1"},
                {"armId": "A1", "epochId": "E2"},
                {"armId": "A2", "epochId": "E1"},
                {"armId": "A2", "epochId": "E2"},
            ],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is True

    def test_missing_pair_fails(self):
        rule = RuleDDF00243()
        design = {
            "id": "D1",
            "arms": [{"id": "A1"}, {"id": "A2"}],
            "epochs": [{"id": "E1"}],
            "studyCells": [{"armId": "A1", "epochId": "E1"}],  # A2/E1 missing
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_duplicate_pair_fails(self):
        rule = RuleDDF00243()
        design = {
            "id": "D1",
            "arms": [{"id": "A1"}],
            "epochs": [{"id": "E1"}],
            "studyCells": [
                {"armId": "A1", "epochId": "E1"},
                {"armId": "A1", "epochId": "E1"},  # duplicate
            ],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_non_dict_cells_and_arms_and_epochs_are_ignored(self):
        rule = RuleDDF00243()
        design = {
            "id": "D1",
            "arms": [None, {"id": "A1"}],
            "epochs": ["scalar", {"id": "E1"}],
            "studyCells": [None, "scalar", {"armId": "A1", "epochId": "E1"}],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is True

    def test_cell_outside_known_arm_epoch_is_ignored(self):
        """A studyCell with armId/epochId not in the known sets is ignored;
        missing valid pair still fails."""
        rule = RuleDDF00243()
        design = {
            "id": "D1",
            "arms": [{"id": "A1"}],
            "epochs": [{"id": "E1"}],
            "studyCells": [{"armId": "UNKNOWN", "epochId": "E1"}],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is False

    def test_observational_design_scope(self):
        rule = RuleDDF00243()
        design = {
            "id": "D2",
            "arms": [{"id": "A1"}],
            "epochs": [{"id": "E1"}],
            "studyCells": [],
        }
        data = self._data({"ObservationalStudyDesign": [design]})
        assert rule.validate({"data": data}) is False
