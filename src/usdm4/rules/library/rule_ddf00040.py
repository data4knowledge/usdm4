from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00040(RuleTemplate):
    """
    DDF00040: Each study element must be referenced by at least one study cell.

    Applies to: StudyCell
    Attributes: elements
    """

    def __init__(self):
        super().__init__(
            "DDF00040",
            RuleTemplate.ERROR,
            "Each study element must be referenced by at least one study cell.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("StudyElement"):
            if not item.get("elements"):
                self._add_failure(
                    "Required attribute 'elements' is missing or empty",
                    "StudyElement",
                    "elements",
                    data.path_by_id(item["id"]),
                )
        return self._result()
