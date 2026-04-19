# MANUAL: do not regenerate
#
# For each StudyAmendment, its primaryReason must not have code.code
# == C48660 ("Not Applicable"). Iterates StudyAmendment to reach the
# primaryReason directly rather than filtering all StudyAmendmentReason
# instances (secondary reasons may legitimately be "not applicable").
from usdm4.rules.rule_template import RuleTemplate


NOT_APPLICABLE_CODE = "C48660"


class RuleDDF00255(RuleTemplate):
    """
    DDF00255: A primary study amendment reason is not expected to be 'not applicable'.

    Applies to: StudyAmendmentReason (when reached via StudyAmendment.primaryReason)
    Attributes: code
    """

    def __init__(self):
        super().__init__(
            "DDF00255",
            RuleTemplate.WARNING,
            "A primary study amendment reason is not expected to be 'not applicable'.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for amendment in data.instances_by_klass("StudyAmendment"):
            primary = amendment.get("primaryReason")
            if not isinstance(primary, dict):
                continue
            code_obj = primary.get("code")
            if not isinstance(code_obj, dict):
                continue
            if code_obj.get("code") == NOT_APPLICABLE_CODE:
                self._add_failure(
                    "Primary StudyAmendmentReason has code 'Not Applicable' (C48660)",
                    "StudyAmendmentReason",
                    "code",
                    data.path_by_id(primary["id"]),
                )
        return self._result()
