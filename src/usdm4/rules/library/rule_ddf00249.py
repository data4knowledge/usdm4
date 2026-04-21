from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00249(RuleTemplate):
    """
    DDF00249: An eligibility criterion item is expected to be used in at least one study design.

    Applies to: EligibilityCriterion
    Attributes: criterionItem
    """

    def __init__(self):
        super().__init__(
            "DDF00249",
            RuleTemplate.WARNING,
            "An eligibility criterion item is expected to be used in at least one study design.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("EligibilityCriterion"):
            if not item.get("criterionItem"):
                self._add_failure(
                    "Required attribute 'criterionItem' is missing or empty",
                    "EligibilityCriterion",
                    "criterionItem",
                    data.path_by_id(item["id"]),
                )
        return self._result()
