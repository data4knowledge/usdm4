# MANUAL: do not regenerate
#
# Self-reference check on the children relationship. In USDM JSON the
# attribute is `childIds` (list of FK strings). Iterates the 5 classes
# that carry a children relationship per the YAML entity list and flags
# any where the instance's own id appears in its own childIds.
from usdm4.rules.rule_template import RuleTemplate


SCOPE_CLASSES = [
    "BiomedicalConceptCategory",
    "StudyProtocolDocumentVersion",
    "StudyDefinitionDocument",
    "NarrativeContent",
    "Activity",
]


class RuleDDF00018(RuleTemplate):
    """
    DDF00018: An instance of a class must not reference itself as one of its own children.

    Applies to: BiomedicalConceptCategory, StudyProtocolDocumentVersion, StudyDefinitionDocument, NarrativeContent, Activity
    Attributes: childIds
    """

    def __init__(self):
        super().__init__(
            "DDF00018",
            RuleTemplate.ERROR,
            "An instance of a class must not reference itself as one of its own children.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in SCOPE_CLASSES:
            for instance in data.instances_by_klass(klass):
                own_id = instance.get("id")
                child_ids = instance.get("childIds") or []
                if own_id and own_id in child_ids:
                    self._add_failure(
                        f"{klass} references itself as one of its own children",
                        klass,
                        "childIds",
                        data.path_by_id(own_id),
                    )
        return self._result()
