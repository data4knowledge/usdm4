# MANUAL: do not regenerate
#
# SubjectEnrollment.quantity is an embedded Quantity. Its unit must be
# absent/empty OR exactly the Percent AliasCode (standardCode with
# codeSystem=http://www.cdisc.org, code=C25613, decode="%").
#
# CORE-000806 is strict on all three: codeSystem, code, AND decode must
# match. A unit with code C25613 but decode="Percentage" (the preferred
# term rather than the "%" submission value) is not acceptable. Earlier
# implementation checked only the code, letting decode="Percentage"
# through — a real sample in validate/sample_usdm.json exhibited this.
from usdm4.rules.rule_template import RuleTemplate


PERCENT_CODE = "C25613"
PERCENT_DECODE = "%"
CDISC_CODE_SYSTEM = "http://www.cdisc.org"


def _is_acceptable_unit(unit):
    # Missing / false / empty-dict unit all count as "no unit specified".
    if unit is None or unit is False:
        return True
    if not isinstance(unit, dict):
        return False
    if not unit:
        return True
    standard = unit.get("standardCode")
    if not isinstance(standard, dict):
        return False
    return (
        standard.get("codeSystem") == CDISC_CODE_SYSTEM
        and standard.get("code") == PERCENT_CODE
        and standard.get("decode") == PERCENT_DECODE
    )


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
                    "SubjectEnrollment.quantity has a unit that is neither "
                    "empty nor the Percent AliasCode "
                    "(codeSystem=http://www.cdisc.org, code=C25613, decode='%')",
                    "SubjectEnrollment",
                    "quantity",
                    data.path_by_id(enrollment["id"]),
                )
        return self._result()
