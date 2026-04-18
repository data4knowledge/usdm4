from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00170(RuleTemplate):
    """
    DDF00170: All abbreviations defined for a study version must be unique.

    Applies to: Abbreviation
    Attributes: abbreviatedText
    """

    def __init__(self):
        super().__init__(
            "DDF00170",
            RuleTemplate.ERROR,
            "All abbreviations defined for a study version must be unique.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        seen: dict = {}
        for item in data.instances_by_klass("Abbreviation"):
            scope = data.parent_by_klass(item["id"], ['StudyVersion'])
            if scope is None:
                continue
            key = (scope["id"], item.get("abbreviatedText"))
            if key in seen:
                self._add_failure(
                    f"Duplicate {item.get('abbreviatedText')!r} within scope",
                    "Abbreviation",
                    "abbreviatedText",
                    data.path_by_id(item["id"]),
                )
            else:
                seen[key] = item["id"]
        return self._result()
