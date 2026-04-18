from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00228(RuleTemplate):
    """
    DDF00228: An observational study (including patient registries) must be specified using the ObservationalStudyDesign class.

    Applies to: ObservationalStudyDesign
    Attributes: studyType
    """

    def __init__(self):
        super().__init__(
            "DDF00228",
            RuleTemplate.ERROR,
            "An observational study (including patient registries) must be specified using the ObservationalStudyDesign class.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("ObservationalStudyDesign"):
            if not item.get("studyType"):
                self._add_failure(
                    "Required attribute 'studyType' is missing or empty",
                    "ObservationalStudyDesign",
                    "studyType",
                    data.path_by_id(item["id"]),
                )
        return self._result()
