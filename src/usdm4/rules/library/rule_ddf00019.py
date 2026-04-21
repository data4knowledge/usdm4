# MANUAL: do not regenerate
#
# Self-reference: SAI / ScheduledDecisionInstance must not name
# itself as its own defaultConditionId.
from usdm4.rules.rule_template import RuleTemplate


SCOPE_CLASSES = ["ScheduledActivityInstance", "ScheduledDecisionInstance"]


class RuleDDF00019(RuleTemplate):
    """
    DDF00019: A scheduled activity/decision instance must not refer to itself as its default condition.

    Applies to: ScheduledActivityInstance, ScheduledDecisionInstance
    Attributes: defaultConditionId
    """

    def __init__(self):
        super().__init__(
            "DDF00019",
            RuleTemplate.ERROR,
            "A scheduled activity/decision instance must not refer to itself as its default condition.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in SCOPE_CLASSES:
            for instance in data.instances_by_klass(klass):
                default_id = instance.get("defaultConditionId")
                if default_id and default_id == instance.get("id"):
                    self._add_failure(
                        f"{klass} refers to itself as its defaultConditionId",
                        klass,
                        "defaultConditionId",
                        data.path_by_id(instance["id"]),
                    )
        return self._result()
