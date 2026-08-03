# MANUAL: do not regenerate
#
# Auto-classified as LOW_CUSTOM by stage-1 — the text-classifier regex for
# the at-least-one-of idiom matches "at least one" but not "at least a".
# Hand-authored. The xlsx attributes column says "members, children" but
# the USDM JSON field names are `memberIds` and `childIds` per
# dataStructure.yml (id-reference lists, cardinality 0..*).
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00014(RuleTemplate):
    """
    DDF00014: A biomedical concept category is expected to have at least a member or a child.

    Applies to: BiomedicalConceptCategory
    Attributes: members, children
    """

    def __init__(self):
        super().__init__(
            "DDF00014",
            RuleTemplate.WARNING,
            "A biomedical concept category is expected to have at least a member or a child.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("BiomedicalConceptCategory"):
            members = item.get("memberIds") or []
            children = item.get("childIds") or []
            if not members and not children:
                self._add_failure(
                    "BiomedicalConceptCategory has neither members nor children",
                    "BiomedicalConceptCategory",
                    "memberIds, childIds",
                    data.path_by_id(item["id"]),
                )
        return self._result()
