from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00097(RuleTemplate):
    """
    DDF00097: Within a study design, the planned age range must be specified either in the study population or in all cohorts.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: plannedAge
    """

    def __init__(self):
        super().__init__(
            "DDF00097",
            RuleTemplate.ERROR,
            "Within a study design, the planned age range must be specified either in the study population or in all cohorts.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("StudyDesignPopulation"):
            if not item.get("plannedAge"):
                self._add_failure(
                    "Required attribute 'plannedAge' is missing or empty",
                    "StudyDesignPopulation",
                    "plannedAge",
                    data.path_by_id(item["id"]),
                )
        return self._result()
