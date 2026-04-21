from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00013(RuleTemplate):
    """
    DDF00013: If a biomedical concept property is required then it must also be enabled, while if it is not enabled then it must not be required.

    Applies to: BiomedicalConceptProperty
    Attributes: isRequired, isEnabled
    """

    def __init__(self):
        super().__init__(
            "DDF00013",
            RuleTemplate.ERROR,
            "If a biomedical concept property is required then it must also be enabled, while if it is not enabled then it must not be required.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("BiomedicalConceptProperty"):
            if (item.get("isRequired") is True) and not (item.get("isEnabled") is True):
                self._add_failure(
                    "isRequired is set but required isEnabled is missing",
                    "BiomedicalConceptProperty",
                    "isRequired, isEnabled",
                    data.path_by_id(item["id"]),
                )
        return self._result()
