"""Tests for RuleDDF00009 — ScheduleTimeline Fixed Reference anchor."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00009 import RuleDDF00009
from usdm4.rules.rule_template import RuleTemplate


def _data(timelines):
    data = MagicMock()
    data.instances_by_klass.return_value = timelines
    data.path_by_id.return_value = "$.path"
    return data


class TestRuleDDF00009:
    def test_metadata(self):
        rule = RuleDDF00009()
        assert rule._rule == "DDF00009"
        assert rule._level == RuleTemplate.ERROR

    def test_anchor_by_code_passes(self):
        """Fixed Reference via CT code C201358."""
        rule = RuleDDF00009()
        data = _data(
            [
                {
                    "id": "T1",
                    "instances": [{"id": "SAI1"}, {"id": "SAI2"}],
                    "timings": [
                        {
                            "type": {"code": "C201358"},
                            "relativeToScheduledInstanceId": "SAI1",
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_anchor_by_decode_passes(self):
        """Fall-back recognition via decode = 'Fixed Reference'."""
        rule = RuleDDF00009()
        data = _data(
            [
                {
                    "id": "T1",
                    "instances": [{"id": "SAI1"}],
                    "timings": [
                        {
                            "type": {"decode": "Fixed Reference"},
                            "relativeToScheduledInstanceId": "SAI1",
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_no_fixed_reference_timing_fails(self):
        rule = RuleDDF00009()
        data = _data(
            [
                {
                    "id": "T1",
                    "instances": [{"id": "SAI1"}],
                    "timings": [
                        {
                            "type": {"decode": "Before"},
                            "relativeToScheduledInstanceId": "SAI1",
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False

    def test_fixed_reference_targets_instance_outside_timeline_fails(self):
        """Regression: Fixed Reference pointing to a SAI NOT in this
        timeline's instances must still fail. CORE's condition compares
        $fixed_ref_sched_ins against THIS timeline's $instances."""
        rule = RuleDDF00009()
        data = _data(
            [
                {
                    "id": "T1",
                    "instances": [{"id": "SAI1"}, {"id": "SAI2"}],
                    "timings": [
                        {
                            "type": {"decode": "Fixed Reference"},
                            # Target is NOT one of this timeline's instances
                            "relativeToScheduledInstanceId": "SAI_elsewhere",
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False

    def test_empty_timings_fails(self):
        rule = RuleDDF00009()
        data = _data([{"id": "T1", "instances": [{"id": "SAI1"}], "timings": []}])
        assert rule.validate({"data": data}) is False

    def test_no_instances_fails(self):
        rule = RuleDDF00009()
        data = _data(
            [
                {
                    "id": "T1",
                    "instances": [],
                    "timings": [
                        {
                            "type": {"decode": "Fixed Reference"},
                            "relativeToScheduledInstanceId": "SAI1",
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False

    def test_uses_correct_class_name(self):
        """Regression: previous impl iterated 'ScheduledTimeline' (typo).
        The class is `ScheduleTimeline`; with the wrong name, the rule
        silently passed every instance."""
        rule = RuleDDF00009()
        data = MagicMock()
        called = []

        def by_klass(k):
            called.append(k)
            return []

        data.instances_by_klass.side_effect = by_klass
        data.path_by_id.return_value = "$.path"
        rule.validate({"data": data})
        assert "ScheduleTimeline" in called

    def test_multiple_timelines_independent(self):
        rule = RuleDDF00009()
        data = _data(
            [
                {
                    "id": "T1",
                    "instances": [{"id": "SAI1"}],
                    "timings": [
                        {
                            "type": {"decode": "Fixed Reference"},
                            "relativeToScheduledInstanceId": "SAI1",
                        }
                    ],
                },
                {"id": "T2", "instances": [{"id": "SAI2"}], "timings": []},
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
