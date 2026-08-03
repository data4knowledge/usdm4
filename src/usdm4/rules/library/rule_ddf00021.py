# MANUAL: do not regenerate
#
# Self-reference check: an instance must not name itself as its previous
# instance. Rule text lists 6 classes that carry a `previous` ordering
# relationship; in USDM JSON this is stored as `previousId`.
from usdm4.rules.rule_template import RuleTemplate


SCOPE_CLASSES = [
    "StudyEpoch",
    "Encounter",
    "Activity",
    "NarrativeContent",
    "EligibilityCriterion",
    "StudyAmendment",
]


class RuleDDF00021(RuleTemplate):
    """
    DDF00021: An instance of a class must not refer to itself as its previous instance.

    Applies to: StudyEpoch, Encounter, Activity, NarrativeContent, EligibilityCriterion, StudyAmendment
    Attributes: previousId
    """

    def __init__(self):
        super().__init__(
            "DDF00021",
            RuleTemplate.ERROR,
            "An instance of a class must not refer to itself as its previous instance.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in SCOPE_CLASSES:
            for instance in data.instances_by_klass(klass):
                previous_id = instance.get("previousId")
                if previous_id and previous_id == instance.get("id"):
                    self._add_failure(
                        f"{klass} refers to itself as its previous instance",
                        klass,
                        "previousId",
                        data.path_by_id(instance["id"]),
                    )
        return self._result()
