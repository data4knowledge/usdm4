from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00193(RuleTemplate):
    """
    DDF00193: A masking is expected to be defined for at least one study role in a study design with a blinding schema that is not open label or double blind.

    Applies to: StudyRole
    Attributes: masking
    """

    def __init__(self):
        super().__init__(
            "DDF00193",
            RuleTemplate.WARNING,
            "A masking is expected to be defined for at least one study role in a study design with a blinding schema that is not open label or double blind.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("StudyRole"):
            if not item.get("masking"):
                self._add_failure(
                    "Required attribute 'masking' is missing or empty",
                    "StudyRole",
                    "masking",
                    data.path_by_id(item["id"]),
                )
        return self._result()
