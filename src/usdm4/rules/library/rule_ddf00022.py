# MANUAL: do not regenerate
#
# Twin of DDF00021: an instance must not name itself as its next instance.
# Rule text lists 5 classes (no StudyAmendment — StudyAmendment only has a
# `previous` relationship per the YAML entity list).
from usdm4.rules.rule_template import RuleTemplate


SCOPE_CLASSES = [
    "StudyEpoch",
    "Encounter",
    "Activity",
    "NarrativeContent",
    "EligibilityCriterion",
]


class RuleDDF00022(RuleTemplate):
    """
    DDF00022: An instance of a class must not refer to itself as its next instance.

    Applies to: StudyEpoch, Encounter, Activity, NarrativeContent, EligibilityCriterion
    Attributes: nextId
    """

    def __init__(self):
        super().__init__(
            "DDF00022",
            RuleTemplate.ERROR,
            "An instance of a class must not refer to itself as its next instance.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in SCOPE_CLASSES:
            for instance in data.instances_by_klass(klass):
                next_id = instance.get("nextId")
                if next_id and next_id == instance.get("id"):
                    self._add_failure(
                        f"{klass} refers to itself as its next instance",
                        klass,
                        "nextId",
                        data.path_by_id(instance["id"]),
                    )
        return self._result()
