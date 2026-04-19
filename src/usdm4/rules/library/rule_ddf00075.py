# MANUAL: do not regenerate
#
# At-least-one-of check: Activity must reference ≥1 of definedProcedures,
# biomedicalConceptIds, bcCategoryIds, or bcSurrogateIds. Activities
# with `childIds` are wrappers (their children do the referencing) and
# shouldn't be flagged.
from usdm4.rules.rule_template import RuleTemplate


LEAF_REF_ATTRS = [
    "definedProcedures",
    "biomedicalConceptIds",
    "bcCategoryIds",
    "bcSurrogateIds",
]


class RuleDDF00075(RuleTemplate):
    """
    DDF00075: An activity is expected to refer to at least one procedure, biomedical concept, biomedical concept category or biomedical concept surrogate.

    Applies to: Activity
    Attributes: definedProcedures, biomedicalConceptIds, bcCategoryIds, bcSurrogateIds
    """

    def __init__(self):
        super().__init__(
            "DDF00075",
            RuleTemplate.WARNING,
            "An activity is expected to refer to at least one procedure, biomedical concept, biomedical concept category or biomedical concept surrogate.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for activity in data.instances_by_klass("Activity"):
            # Wrapper activities with children aren't expected to carry leaf refs
            if activity.get("childIds"):
                continue
            if not any(activity.get(a) for a in LEAF_REF_ATTRS):
                self._add_failure(
                    "Activity does not reference any procedure, BC, BC category, or BC surrogate",
                    "Activity",
                    ", ".join(LEAF_REF_ATTRS),
                    data.path_by_id(activity["id"]),
                )
        return self._result()
