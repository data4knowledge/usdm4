from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00133(RuleTemplate):
    """
    DDF00133: Within a study design, if a planned enrollment number is defined, it must be specified either in the study population or in all cohorts.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: plannedEnrollmentNumber
    """

    def __init__(self):
        super().__init__(
            "DDF00133",
            RuleTemplate.ERROR,
            "Within a study design, if a planned enrollment number is defined, it must be specified either in the study population or in all cohorts.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("StudyDesignPopulation"):
            if not item.get("plannedEnrollmentNumber"):
                self._add_failure(
                    "Required attribute 'plannedEnrollmentNumber' is missing or empty",
                    "StudyDesignPopulation",
                    "plannedEnrollmentNumber",
                    data.path_by_id(item["id"]),
                )
        return self._result()
