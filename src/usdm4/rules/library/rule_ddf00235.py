# MANUAL: do not regenerate
#
# Twin of DDF00234 but for plannedCompletionNumber on
# StudyDesignPopulation / StudyCohort. No unit expected on either the
# Quantity or the Range representation.
from usdm4.rules.rule_template import RuleTemplate


SCOPE_CLASSES = ["StudyDesignPopulation", "StudyCohort"]
ATTRIBUTE = "plannedCompletionNumber"


class RuleDDF00235(RuleTemplate):
    """
    DDF00235: A unit must not be specified for a planned completion number.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: plannedCompletionNumber
    """

    def __init__(self):
        super().__init__(
            "DDF00235",
            RuleTemplate.ERROR,
            "A unit must not be specified for a planned completion number.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in SCOPE_CLASSES:
            for instance in data.instances_by_klass(klass):
                self._check_quantity_or_range(data, klass, instance)
        return self._result()

    def _check_quantity_or_range(self, data, klass, instance):
        number = instance.get(ATTRIBUTE)
        if not isinstance(number, dict):
            return
        if number.get("unit"):
            self._add_failure(
                f"{klass}.{ATTRIBUTE} has a unit; none expected for a planned completion number",
                klass,
                ATTRIBUTE,
                data.path_by_id(instance["id"]),
            )
        for endpoint_name in ("minValue", "maxValue"):
            endpoint = number.get(endpoint_name)
            if isinstance(endpoint, dict) and endpoint.get("unit"):
                self._add_failure(
                    f"{klass}.{ATTRIBUTE}.{endpoint_name} has a unit; none expected for a planned completion number",
                    klass,
                    ATTRIBUTE,
                    data.path_by_id(instance["id"]),
                )
