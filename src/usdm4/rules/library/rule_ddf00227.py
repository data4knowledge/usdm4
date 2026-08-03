from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00227(RuleTemplate):
    """
    DDF00227: An interventional study must be specified using the InterventionalStudyDesign class.

    Applies to: InterventionalStudyDesign
    Attributes: studyType
    """

    def __init__(self):
        super().__init__(
            "DDF00227",
            RuleTemplate.ERROR,
            "An interventional study must be specified using the InterventionalStudyDesign class.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("InterventionalStudyDesign"):
            if not item.get("studyType"):
                self._add_failure(
                    "Required attribute 'studyType' is missing or empty",
                    "InterventionalStudyDesign",
                    "studyType",
                    data.path_by_id(item["id"]),
                )
        return self._result()
