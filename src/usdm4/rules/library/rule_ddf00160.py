# MANUAL: do not regenerate
#
# Activity mutex: if childIds is non-empty, none of
# {biomedicalConceptIds, bcCategoryIds, bcSurrogateIds, timelineId,
# definedProcedures} may be populated. CORE groups these into one
# $ActivityDetails boolean and fails when both childIds and details
# are set.
from usdm4.rules.rule_template import RuleTemplate


LEAF_REF_ATTRS = [
    "biomedicalConceptIds",
    "bcCategoryIds",
    "bcSurrogateIds",
    "timelineId",
    "definedProcedures",
]


def _is_populated(value):
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


class RuleDDF00160(RuleTemplate):
    """
    DDF00160: An activity with children must not refer to a timeline, procedure, biomedical concept, biomedical concept category or biomedical concept surrogate.

    Applies to: Activity
    Attributes: childIds + {biomedicalConceptIds, bcCategoryIds, bcSurrogateIds, timelineId, definedProcedures}
    """

    def __init__(self):
        super().__init__(
            "DDF00160",
            RuleTemplate.ERROR,
            "An activity with children must not refer to a timeline, procedure, biomedical concept, biomedical concept category or biomedical concept surrogate.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for activity in data.instances_by_klass("Activity"):
            children = activity.get("childIds") or []
            if not children:
                continue
            populated_refs = [
                a for a in LEAF_REF_ATTRS if _is_populated(activity.get(a))
            ]
            if populated_refs:
                self._add_failure(
                    f"Activity has children but also references: {', '.join(populated_refs)}",
                    "Activity",
                    "childIds, " + ", ".join(LEAF_REF_ATTRS),
                    data.path_by_id(activity["id"]),
                )
        return self._result()
