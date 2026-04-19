# MANUAL: do not regenerate
#
# For each Activity: build the set of BCs it directly references
# (biomedicalConceptIds) and the set of BCs it transitively references
# through bcCategoryIds (union of memberIds over each BCCategory).
# The intersection of the two sets must be empty.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00076(RuleTemplate):
    """
    DDF00076: If a biomedical concept is referenced from an activity then it is not expected to be referenced as well by a biomedical concept category that is referenced from the same activity.

    Applies to: Activity, BiomedicalConceptCategory
    Attributes: biomedicalConceptIds, bcCategoryIds
    """

    def __init__(self):
        super().__init__(
            "DDF00076",
            RuleTemplate.WARNING,
            "If a biomedical concept is referenced from an activity then it is not expected to be referenced as well by a biomedical concept category that is referenced from the same activity.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for activity in data.instances_by_klass("Activity"):
            direct = set(activity.get("biomedicalConceptIds") or [])
            if not direct:
                continue
            via_category: set = set()
            for cat_id in activity.get("bcCategoryIds") or []:
                cat = data.instance_by_id(cat_id)
                if isinstance(cat, dict):
                    for member_id in cat.get("memberIds") or []:
                        via_category.add(member_id)
            overlap = direct & via_category
            if overlap:
                self._add_failure(
                    f"Activity references BC(s) {sorted(overlap)} both directly and through a BC Category it also references",
                    "Activity",
                    "biomedicalConceptIds, bcCategoryIds",
                    data.path_by_id(activity["id"]),
                )
        return self._result()
