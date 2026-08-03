# MANUAL: do not regenerate
#
# Condition.contextIds is a list of FK strings that must each resolve
# to an existing instance whose instanceType is Activity or
# ScheduledActivityInstance. The failure covers both cases: the id
# doesn't exist, OR it exists but points to the wrong class.
from usdm4.rules.rule_template import RuleTemplate


ALLOWED_CONTEXT_CLASSES = {"Activity", "ScheduledActivityInstance"}


class RuleDDF00114(RuleTemplate):
    """
    DDF00114: If specified, the context of a condition must point to a valid instance in the activity or scheduled activity instance class.

    Applies to: Condition
    Attributes: contextIds
    """

    def __init__(self):
        super().__init__(
            "DDF00114",
            RuleTemplate.ERROR,
            "If specified, the context of a condition must point to a valid instance in the activity or scheduled activity instance class.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for condition in data.instances_by_klass("Condition"):
            for context_id in condition.get("contextIds") or []:
                if not context_id:
                    continue
                target = data.instance_by_id(context_id)
                target_type = (
                    target.get("instanceType") if isinstance(target, dict) else None
                )
                if target_type not in ALLOWED_CONTEXT_CLASSES:
                    reason = (
                        "does not resolve to any instance"
                        if target is None
                        else f"resolves to {target_type} (not Activity or ScheduledActivityInstance)"
                    )
                    self._add_failure(
                        f"Condition.contextIds entry {context_id!r} {reason}",
                        "Condition",
                        "contextIds",
                        data.path_by_id(condition["id"]),
                    )
        return self._result()
