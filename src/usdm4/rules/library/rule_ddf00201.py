# MANUAL: do not regenerate
#
# Cardinality rule: exactly one StudyRole per StudyVersion must have the
# sponsor code C70793. Close sibling of DDF00172 (exactly one sponsor
# study identifier) and DDF00202 (sponsor role points to exactly one org).
from usdm4.rules.rule_template import RuleTemplate


SPONSOR_ROLE_CODE = "C70793"


class RuleDDF00201(RuleTemplate):
    """
    DDF00201: There must be exactly one study role with a code of sponsor.

    Applies to: StudyRole
    Attributes: code
    """

    def __init__(self):
        super().__init__(
            "DDF00201",
            RuleTemplate.ERROR,
            "There must be exactly one study role with a code of sponsor.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sv in data.instances_by_klass("StudyVersion"):
            count = 0
            for role in sv.get("roles") or []:
                code = role.get("code") or {}
                if isinstance(code, dict) and code.get("code") == SPONSOR_ROLE_CODE:
                    count += 1
            if count != 1:
                self._add_failure(
                    f"Expected exactly one sponsor study role, found {count}",
                    "StudyVersion",
                    "roles",
                    data.path_by_id(sv["id"]),
                )
        return self._result()
