from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00164(RuleTemplate):
    """
    DDF00164: If a section number is to be displayed then a number must be specified and vice versa.

    Applies to: NarrativeContent
    Attributes: sectionNumber, displaySectionNumber
    """

    def __init__(self):
        super().__init__(
            "DDF00164",
            RuleTemplate.ERROR,
            "If a section number is to be displayed then a number must be specified and vice versa.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("NarrativeContent"):
            a = (item.get("displaySectionNumber") is True)
            b = bool(item.get("sectionNumber"))
            if a != b:
                if a and not b:
                    msg = "displaySectionNumber is set but sectionNumber is missing"
                else:
                    msg = "sectionNumber is set but displaySectionNumber is missing"
                self._add_failure(
                    msg,
                    "NarrativeContent",
                    "displaySectionNumber, sectionNumber",
                    data.path_by_id(item["id"]),
                )
        return self._result()
