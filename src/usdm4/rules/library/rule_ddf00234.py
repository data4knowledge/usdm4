# MANUAL: do not regenerate
#
# plannedEnrollmentNumber is an embedded Quantity or Range on
# StudyDesignPopulation / StudyCohort. Unit must NOT be present on
# whichever representation is used (Quantity.unit, or Range's
# minValue.unit / maxValue.unit). "Specified" = any non-None value.
from usdm4.rules.rule_template import RuleTemplate


SCOPE_CLASSES = ["StudyDesignPopulation", "StudyCohort"]
ATTRIBUTE = "plannedEnrollmentNumber"


class RuleDDF00234(RuleTemplate):
    """
    DDF00234: A unit must not be specified for a planned enrollment number.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: plannedEnrollmentNumber
    """

    def __init__(self):
        super().__init__(
            "DDF00234",
            RuleTemplate.ERROR,
            "A unit must not be specified for a planned enrollment number.",
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
        # Quantity case
        if number.get("unit"):
            self._add_failure(
                f"{klass}.{ATTRIBUTE} has a unit; none expected for a planned enrollment number",
                klass,
                ATTRIBUTE,
                data.path_by_id(instance["id"]),
            )
        # Range case
        for endpoint_name in ("minValue", "maxValue"):
            endpoint = number.get(endpoint_name)
            if isinstance(endpoint, dict) and endpoint.get("unit"):
                self._add_failure(
                    f"{klass}.{ATTRIBUTE}.{endpoint_name} has a unit; none expected for a planned enrollment number",
                    klass,
                    ATTRIBUTE,
                    data.path_by_id(instance["id"]),
                )
