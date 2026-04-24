from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00165(RuleTemplate):
    """
    DDF00165: If a section title is to be displayed then a title must be specified and vice versa.

    Applies to: NarrativeContent
    Attributes: sectionTitle, displaySectionTitle
    """

    def __init__(self):
        super().__init__(
            "DDF00165",
            RuleTemplate.ERROR,
            "If a section title is to be displayed then a title must be specified and vice versa.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("NarrativeContent"):
            a = item.get("displaySectionTitle") is True
            b = bool(item.get("sectionTitle"))
            if a != b:
                if a and not b:
                    msg = "displaySectionTitle is set but sectionTitle is missing"
                else:
                    msg = "sectionTitle is set but displaySectionTitle is missing"
                self._add_failure(
                    msg,
                    "NarrativeContent",
                    "displaySectionTitle, sectionTitle",
                    data.path_by_id(item["id"]),
                )
        return self._result()
