from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00030(RuleTemplate):
    """
    DDF00030: At least the text or the family name must be specified for a person name.

    Applies to: PersonName
    Attributes: text, familyName
    """

    def __init__(self):
        super().__init__(
            "DDF00030",
            RuleTemplate.ERROR,
            "At least the text or the family name must be specified for a person name.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("PersonName"):
            if not item.get("text"):
                self._add_failure(
                    "Required attribute 'text' is missing or empty",
                    "PersonName",
                    "text",
                    data.path_by_id(item["id"]),
                )
        return self._result()
