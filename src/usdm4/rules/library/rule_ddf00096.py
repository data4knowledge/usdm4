# MANUAL: do not regenerate
#
# Endpoints live embedded under Objective.endpoints in USDM JSON, so
# every Endpoint already has a parent Objective. The check: a "primary"
# Endpoint (level.code == C94496) must have a parent Objective whose
# level.code == C85826 (Trial Primary Objective).
from usdm4.rules.rule_template import RuleTemplate


PRIMARY_ENDPOINT_CODE = "C94496"
PRIMARY_OBJECTIVE_CODE = "C85826"


class RuleDDF00096(RuleTemplate):
    """
    DDF00096: All primary endpoints must be referenced by a primary objective.

    Applies to: Endpoint
    Attributes: level
    """

    def __init__(self):
        super().__init__(
            "DDF00096",
            RuleTemplate.ERROR,
            "All primary endpoints must be referenced by a primary objective.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for endpoint in data.instances_by_klass("Endpoint"):
            level = endpoint.get("level")
            if not isinstance(level, dict) or level.get("code") != PRIMARY_ENDPOINT_CODE:
                continue
            objective = data.parent_by_klass(endpoint.get("id"), "Objective")
            if not isinstance(objective, dict):
                self._add_failure(
                    "Primary Endpoint has no parent Objective",
                    "Endpoint",
                    "level",
                    data.path_by_id(endpoint["id"]),
                )
                continue
            obj_level = objective.get("level")
            if not isinstance(obj_level, dict) or obj_level.get("code") != PRIMARY_OBJECTIVE_CODE:
                self._add_failure(
                    "Primary Endpoint is under an Objective that is not a primary objective",
                    "Endpoint",
                    "level",
                    data.path_by_id(endpoint["id"]),
                )
        return self._result()
