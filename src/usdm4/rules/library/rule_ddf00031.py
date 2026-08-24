# MANUAL: do not regenerate
#
# Timing type is matched on the CDISC code via
# usdm4.rules.timing.is_fixed_reference, not on a decode string. The
# generated body compared `type["decode"] == "Fixed Reference"`, which never
# matches real data: C201358's preferredTerm is "Fixed Reference Timing Type"
# and the builder writes `decode` from the preferred term.
#
# Effect of the defect: the guard used `!=`, so it was always true and the
# rule ran on the anchor timings it was written to skip, reporting a false
# positive for every Fixed Reference timing.
from usdm4.rules.rule_template import RuleTemplate
from usdm4.rules.timing import is_fixed_reference



class RuleDDF00031(RuleTemplate):
    """
    DDF00031: If timing type is not "Fixed Reference" then it must point to two scheduled instances (e.g. the relativeFromScheduledInstance and relativeToScheduledInstance attributes must not be missing and must not be equal to each other).

    Applies to: Timing
    Attributes: relativeToScheduledInstance
    """

    def __init__(self):
        super().__init__(
            "DDF00031",
            RuleTemplate.ERROR,
            'If timing type is not "Fixed Reference" then it must point to two scheduled instances (e.g. the relativeFromScheduledInstance and relativeToScheduledInstance attributes must not be missing and must not be equal to each other).',
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("Timing"):
            if is_fixed_reference(item):
                continue
            check = True
            if "relativeToScheduledInstanceId" not in item:
                self._add_failure(
                    "Missing relativeToScheduledInstanceId",
                    "Timing",
                    "relativeToScheduledInstanceId",
                    data.path_by_id(item["id"]),
                )
                check = False
            if "relativeFromScheduledInstanceId" not in item:
                self._add_failure(
                    "Missing relativeFromScheduledInstanceId",
                    "Timing",
                    "relativeFromScheduledInstanceId",
                    data.path_by_id(item["id"]),
                )
                check = False
            if (
                check
                and item["relativeToScheduledInstanceId"]
                == item["relativeFromScheduledInstanceId"]
            ):
                self._add_failure(
                    "relativeToScheduledInstanceId and relativeFromScheduledInstanceId are equal",
                    "Timing",
                    "relativeToScheduledInstanceId and relativeFromScheduledInstanceId",
                    data.path_by_id(item["id"]),
                )
        return self._result()
