from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00171(RuleTemplate):
    """
    DDF00171: The expanded text for all abbreviations defined for a study version are expected to be unique.

    Applies to: Abbreviation
    Attributes: expandedText
    """

    def __init__(self):
        super().__init__(
            "DDF00171",
            RuleTemplate.WARNING,
            "The expanded text for all abbreviations defined for a study version are expected to be unique.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        seen: dict = {}
        for item in data.instances_by_klass("Abbreviation"):
            scope = data.parent_by_klass(item["id"], ['StudyVersion'])
            if scope is None:
                continue
            value = item.get("expandedText")
            if value in (None, "", [], {}):
                continue
            key = (scope["id"], value)
            if key in seen:
                self._add_failure(
                    f"Duplicate expandedText {value!r} within scope",
                    "Abbreviation",
                    "expandedText",
                    data.path_by_id(item["id"]),
                )
            else:
                seen[key] = item["id"]
        return self._result()
