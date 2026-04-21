# MANUAL: do not regenerate
#
# Per-amendment check: for each StudyAmendment, no secondaryReasons entry
# may share its Code.code with the primaryReason's Code.code. The rule's
# scope class is StudyAmendmentReason but the comparison needs the
# containing StudyAmendment — we iterate amendments and report against
# the offending secondary reason.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00256(RuleTemplate):
    """
    DDF00256: The same reason is not expected to be given as a primary and secondary reason.

    Applies to: StudyAmendmentReason
    Attributes: code
    """

    def __init__(self):
        super().__init__(
            "DDF00256",
            RuleTemplate.WARNING,
            "The same reason is not expected to be given as a primary and secondary reason.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for amendment in data.instances_by_klass("StudyAmendment"):
            primary = amendment.get("primaryReason")
            secondaries = amendment.get("secondaryReasons") or []
            if not isinstance(primary, dict):
                continue
            primary_code = (primary.get("code") or {}).get("code") if isinstance(primary.get("code"), dict) else None
            if primary_code is None:
                continue
            for secondary in secondaries:
                if not isinstance(secondary, dict):
                    continue
                sec_code_obj = secondary.get("code")
                sec_code = sec_code_obj.get("code") if isinstance(sec_code_obj, dict) else None
                if sec_code == primary_code:
                    self._add_failure(
                        "StudyAmendmentReason given as a secondary reason has the same code as the primary reason",
                        "StudyAmendmentReason",
                        "code",
                        data.path_by_id(secondary["id"]),
                    )
        return self._result()
