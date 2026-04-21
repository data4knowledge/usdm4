# MANUAL: do not regenerate
#
# For Timing instances where type.code == C201358 ("Fixed Reference"),
# relativeToScheduledInstanceId must be either absent/empty OR equal
# to relativeFromScheduledInstanceId. Any other value is a failure —
# it would mean the fixed-reference timing points at two different
# instances.
from usdm4.rules.rule_template import RuleTemplate


FIXED_REFERENCE_CODE = "C201358"


class RuleDDF00007(RuleTemplate):
    """
    DDF00007: If timing type is "Fixed Reference" then it must point to only one scheduled instance (e.g. attribute relativeToScheduledInstance must be equal to relativeFromScheduledInstance or it must be missing).

    Applies to: Timing
    Attributes: relativeToScheduledInstanceId
    """

    def __init__(self):
        super().__init__(
            "DDF00007",
            RuleTemplate.ERROR,
            'If timing type is "Fixed Reference" then it must point to only one scheduled instance (e.g. attribute relativeToScheduledInstance must be equal to relativeFromScheduledInstance or it must be missing).',
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for timing in data.instances_by_klass("Timing"):
            type_obj = timing.get("type")
            if not isinstance(type_obj, dict):
                continue
            if type_obj.get("code") != FIXED_REFERENCE_CODE:
                continue
            to_id = timing.get("relativeToScheduledInstanceId")
            from_id = timing.get("relativeFromScheduledInstanceId")
            if not to_id:
                continue  # absent is allowed
            if to_id == from_id:
                continue  # equal to the from-id is allowed
            self._add_failure(
                f"Fixed-Reference Timing has relativeToScheduledInstanceId {to_id!r} that differs from relativeFromScheduledInstanceId {from_id!r}",
                "Timing",
                "relativeToScheduledInstanceId",
                data.path_by_id(timing["id"]),
            )
        return self._result()
