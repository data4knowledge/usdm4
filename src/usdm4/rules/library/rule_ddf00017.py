# MANUAL: do not regenerate
#
# SubjectEnrollment.quantity is an embedded Quantity. Its unit must be
# absent/empty OR a Percent code (C25613). CORE accepts false / null /
# missing for the unit and an embedded Code with code == "C25613".
from usdm4.rules.rule_template import RuleTemplate


PERCENT_CODE = "C25613"


def _is_acceptable_unit(unit):
    if unit is None or unit is False:
        return True
    if not isinstance(unit, dict):
        return False
    if not unit:
        return True
    standard = unit.get("standardCode")
    if isinstance(standard, dict) and standard.get("code") == PERCENT_CODE:
        return True
    return False


class RuleDDF00017(RuleTemplate):
    """
    DDF00017: Within subject enrollment, the quantity must be a number or a percentage (i.e. the unit must be empty or %).

    Applies to: SubjectEnrollment
    Attributes: quantity
    """

    def __init__(self):
        super().__init__(
            "DDF00017",
            RuleTemplate.ERROR,
            "Within subject enrollment, the quantity must be a number or a percentage (i.e. the unit must be empty or %).",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for enrollment in data.instances_by_klass("SubjectEnrollment"):
            quantity = enrollment.get("quantity")
            if not isinstance(quantity, dict):
                continue
            if not _is_acceptable_unit(quantity.get("unit")):
                self._add_failure(
                    "SubjectEnrollment.quantity has a unit that is neither empty nor Percent (C25613)",
                    "SubjectEnrollment",
                    "quantity",
                    data.path_by_id(enrollment["id"]),
                )
        return self._result()
