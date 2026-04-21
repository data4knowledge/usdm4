# MANUAL: do not regenerate
#
# ConditionAssignment sits inside its parent instance (typically a
# ScheduledDecisionInstance in USDM samples — but we don't need to hard-code
# the parent class). Its `conditionTargetId` must not equal the id of the
# instance that owns it. DataStore's private `_parent` dict gives us the
# immediate container; there is no public API for that.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00044(RuleTemplate):
    """
    DDF00044: The target for a condition must not be equal to its parent.

    Applies to: ConditionAssignment
    Attributes: conditionTargetId
    """

    def __init__(self):
        super().__init__(
            "DDF00044",
            RuleTemplate.ERROR,
            "The target for a condition must not be equal to its parent.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for assignment in data.instances_by_klass("ConditionAssignment"):
            target_id = assignment.get("conditionTargetId")
            if not target_id:
                continue
            parent = data._parent.get(assignment.get("id"))
            if parent is None:
                continue
            if target_id == parent.get("id"):
                self._add_failure(
                    "ConditionAssignment.conditionTargetId equals the id of its parent instance",
                    "ConditionAssignment",
                    "conditionTargetId",
                    data.path_by_id(assignment["id"]),
                )
        return self._result()
