# MANUAL: do not regenerate
#
# Cardinality rule: within each StudyDesign, at least one Endpoint across
# all objectives must have level.code = C94496 (Primary Endpoint — same
# C-code family used by rule_ddf00084 for Primary Objective, and matching
# CORE-001036's JSONata `$count(objectives.endpoints[level.code="C94496"])`).
# Previous implementation only checked that every Endpoint had *some* level
# set, not that any were Primary.
from usdm4.rules.rule_template import RuleTemplate


STUDY_DESIGN_CLASSES = ["InterventionalStudyDesign", "ObservationalStudyDesign"]
PRIMARY_ENDPOINT_CODE = "C94496"


class RuleDDF00041(RuleTemplate):
    """
    DDF00041: Within a study design, there must be at least one endpoint with level primary.

    Applies to: Endpoint
    Attributes: level
    """

    def __init__(self):
        super().__init__(
            "DDF00041",
            RuleTemplate.ERROR,
            "Within a study design, there must be at least one endpoint with level primary.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sd_cls in STUDY_DESIGN_CLASSES:
            for sd in data.instances_by_klass(sd_cls):
                primary_count = 0
                for objective in sd.get("objectives") or []:
                    for endpoint in objective.get("endpoints") or []:
                        level = endpoint.get("level") or {}
                        if (
                            isinstance(level, dict)
                            and level.get("code") == PRIMARY_ENDPOINT_CODE
                        ):
                            primary_count += 1
                if primary_count < 1:
                    self._add_failure(
                        f"Expected at least one Primary Endpoint in study design, found {primary_count}",
                        sd_cls,
                        "objectives.endpoints.level",
                        data.path_by_id(sd["id"]),
                    )
        return self._result()
