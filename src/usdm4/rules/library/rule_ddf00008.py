# MANUAL: do not regenerate
#
# XOR check over (defaultConditionId, timelineExitId): exactly one must
# be specified. CORE-000404 flags both edges — BOTH empty and BOTH
# non-empty. Previous implementation only caught the BOTH-set case, and
# even then required resolving each id to a full instance before flagging
# (which hid bugs where the id pointed to nothing). Sample 3 exposes the
# missed BOTH-empty case — 4 findings CORE catches that d4k passed over.
from usdm4.rules.rule_template import RuleTemplate


def _is_set(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    return bool(value)


class RuleDDF00008(RuleTemplate):
    """
    DDF00008: A scheduled activity instance must refer to either a default condition or a timeline exit, but not both.

    Applies to: ScheduledActivityInstance
    Attributes: timelineExit, defaultCondition
    """

    def __init__(self):
        super().__init__(
            "DDF00008",
            RuleTemplate.ERROR,
            "A scheduled activity instance must refer to either a default condition or a timeline exit, but not both.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("ScheduledActivityInstance"):
            has_condition = _is_set(item.get("defaultConditionId"))
            has_exit = _is_set(item.get("timelineExitId"))
            if has_condition and has_exit:
                self._add_failure(
                    "Both defaultConditionId and timelineExitId are "
                    "specified; set exactly one",
                    "ScheduledActivityInstance",
                    "defaultConditionId, timelineExitId",
                    data.path_by_id(item["id"]),
                )
            elif not has_condition and not has_exit:
                self._add_failure(
                    "Neither defaultConditionId nor timelineExitId is "
                    "specified; set exactly one",
                    "ScheduledActivityInstance",
                    "defaultConditionId, timelineExitId",
                    data.path_by_id(item["id"]),
                )
        return self._result()
