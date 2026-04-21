# MANUAL: do not regenerate
#
# If a GovernanceDate has any geographic scope marked global (C68846),
# the total number of geographic scopes on that date must be exactly 1.
from usdm4.rules.rule_template import RuleTemplate


GLOBAL_CODE = "C68846"


class RuleDDF00151(RuleTemplate):
    """
    DDF00151: If geographic scope type is global then there must be only one geographic scope specified.

    Applies to: GovernanceDate
    Attributes: geographicScopes
    """

    def __init__(self):
        super().__init__(
            "DDF00151",
            RuleTemplate.ERROR,
            "If geographic scope type is global then there must be only one geographic scope specified.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for date in data.instances_by_klass("GovernanceDate"):
            scopes = date.get("geographicScopes") or []
            has_global = any(
                (s.get("type") or {}).get("code") == GLOBAL_CODE
                for s in scopes
                if isinstance(s, dict)
            )
            if has_global and len(scopes) != 1:
                self._add_failure(
                    f"GovernanceDate has a global geographic scope but {len(scopes)} scopes total (must be exactly 1 when global)",
                    "GovernanceDate",
                    "geographicScopes",
                    data.path_by_id(date["id"]),
                )
        return self._result()
