# MANUAL: do not regenerate
#
# Timing type is matched on the CDISC code via
# usdm4.rules.timing.is_fixed_reference, not on a decode string. The
# generated body compared `type["decode"] == "Fixed Reference"`, which never
# matches real data: C201358's preferredTerm is "Fixed Reference Timing Type"
# and the builder writes `decode` from the preferred term.
#
# Effect of the defect: the guard used `==`, so this rule never fired and
# passed silently on every file.
from usdm4.rules.rule_template import RuleTemplate
from usdm4.rules.timing import is_fixed_reference



class RuleDDF00011(RuleTemplate):
    """
    DDF00011: Anchor timings (e.g. type is "Fixed Reference") must be related to a scheduled activity instance via a relativeFromScheduledInstance relationship.

    Applies to: Timing
    Attributes: relativeFromScheduledInstance
    """

    def __init__(self):
        super().__init__(
            "DDF00011",
            RuleTemplate.ERROR,
            'Anchor timings (e.g. type is "Fixed Reference") must be related to a scheduled activity instance via a relativeFromScheduledInstance relationship.',
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("Timing"):
            if not is_fixed_reference(item):
                continue
            if "relativeFromScheduledInstanceId" not in item:
                self._add_failure(
                    "Missing relativeFromScheduledInstance",
                    "Timing",
                    "relativeFromScheduledInstanceId",
                    data.path_by_id(item["id"]),
                )
        return self._result()
