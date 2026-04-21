from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00020(RuleTemplate):
    """
    DDF00020: If the reason for a study amendment is 'Other' then this must be specified (attribute reasonOther must be completed), and vice versa.

    Applies to: StudyAmendmentReason
    Attributes: code, otherReason
    """

    def __init__(self):
        super().__init__(
            "DDF00020",
            RuleTemplate.ERROR,
            "If the reason for a study amendment is 'Other' then this must be specified (attribute reasonOther must be completed), and vice versa.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("StudyAmendmentReason"):
            a = (isinstance(item.get("code"), dict) and item["code"].get("code") == "C17649")
            b = bool(item.get("otherReason"))
            if a != b:
                if a and not b:
                    msg = "code is set but otherReason is missing"
                else:
                    msg = "otherReason is set but code is missing"
                self._add_failure(
                    msg,
                    "StudyAmendmentReason",
                    "code, otherReason",
                    data.path_by_id(item["id"]),
                )
        return self._result()
