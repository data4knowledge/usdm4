# MANUAL: do not regenerate
#
# Rule text: "An eligibility criterion item is expected to be used in at
# least one study design." — i.e. iterate EligibilityCriterionItem
# instances and check each is referenced by ``criterionItemId`` on at
# least one EligibilityCriterion (anywhere in the model).
#
# The previous implementation iterated EligibilityCriterion and checked
# ``item.get("criterionItem")``, but the API model has no such field —
# the link is ``criterionItemId``. As a result the rule fired on every
# criterion regardless of data. This rewrite mirrors what the rule text
# describes (and what CORE typically expresses for the same constraint).
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00249(RuleTemplate):
    """
    DDF00249: An eligibility criterion item is expected to be used in at least one study design.

    Applies to: EligibilityCriterionItem
    Attributes: id
    """

    def __init__(self):
        super().__init__(
            "DDF00249",
            RuleTemplate.WARNING,
            "An eligibility criterion item is expected to be used in at least one study design.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        # Collect every criterionItemId referenced by any EligibilityCriterion
        # in the model. A criterion item is "used" if its id appears in this
        # set.
        used_ids: set[str] = set()
        for criterion in data.instances_by_klass("EligibilityCriterion"):
            ref = criterion.get("criterionItemId")
            if isinstance(ref, str) and ref:
                used_ids.add(ref)
        for item in data.instances_by_klass("EligibilityCriterionItem"):
            iid = item.get("id")
            if not iid or iid in used_ids:
                continue
            self._add_failure(
                "EligibilityCriterionItem is not used by any EligibilityCriterion",
                "EligibilityCriterionItem",
                "id",
                data.path_by_id(iid),
            )
        return self._result()
