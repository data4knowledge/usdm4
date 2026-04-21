# MANUAL: do not regenerate
#
# For each StudyVersion, any role with code.code == C70793 ("Sponsor")
# must have the StudyVersion's id in its appliesToIds.
from usdm4.rules.rule_template import RuleTemplate


SPONSOR_ROLE_CODE = "C70793"


class RuleDDF00203(RuleTemplate):
    """
    DDF00203: The sponsor study role must be applicable to a study version.

    Applies to: StudyRole
    Attributes: appliesToIds
    """

    def __init__(self):
        super().__init__(
            "DDF00203",
            RuleTemplate.ERROR,
            "The sponsor study role must be applicable to a study version.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sv in data.instances_by_klass("StudyVersion"):
            sv_id = sv.get("id")
            for role in sv.get("roles") or []:
                if not isinstance(role, dict):
                    continue
                code = role.get("code")
                if not (isinstance(code, dict) and code.get("code") == SPONSOR_ROLE_CODE):
                    continue
                applies = role.get("appliesToIds") or []
                if sv_id not in applies:
                    self._add_failure(
                        "Sponsor StudyRole is not applicable to the StudyVersion",
                        "StudyRole",
                        "appliesToIds",
                        data.path_by_id(role["id"]),
                    )
        return self._result()
