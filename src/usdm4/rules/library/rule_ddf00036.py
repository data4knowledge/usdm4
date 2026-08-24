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



class RuleDDF00036(RuleTemplate):
    """
    DDF00036: If timing type is "Fixed Reference" then the corresponding attribute relativeToFrom must be filled with "Start to Start".

    Applies to: Timing
    Attributes: relativeToFrom
    """

    def __init__(self):
        super().__init__(
            "DDF00036",
            RuleTemplate.ERROR,
            'If timing type is "Fixed Reference" then the corresponding attribute relativeToFrom must be filled with "Start to Start".',
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("Timing"):
            if not is_fixed_reference(item):
                continue
            to_from = item.get("relativeToFrom")
            if (
                not isinstance(to_from, dict)
                or to_from.get("decode") != "Start to Start"
            ):
                self._add_failure(
                    "Invalid relativeToFrom",
                    "Timing",
                    "relativeToFrom",
                    data.path_by_id(item["id"]),
                )
        return self._result()
