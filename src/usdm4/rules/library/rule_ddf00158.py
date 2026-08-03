from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00158(RuleTemplate):
    """
    DDF00158: Each defined eligibility criterion must be used by at least one study population or cohort within the same study design.

    Applies to: ObservationalStudyDesign, InterventionalStudyDesign
    Attributes: criteria
    """

    def __init__(self):
        super().__init__(
            "DDF00158",
            RuleTemplate.ERROR,
            "Each defined eligibility criterion must be used by at least one study population or cohort within the same study design.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("ObservationalStudyDesign"):
            if not item.get("criteria"):
                self._add_failure(
                    "Required attribute 'criteria' is missing or empty",
                    "ObservationalStudyDesign",
                    "criteria",
                    data.path_by_id(item["id"]),
                )
        return self._result()
