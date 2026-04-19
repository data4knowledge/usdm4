# MANUAL: do not regenerate
#
# Doubly-linked-list consistency. For each instance I with a
# previousId pointing at A: A.nextId (if set) must equal I.id.
# Mirror for nextId → B: B.previousId (if set) must equal I.id.
# The rule only fires when both sides of the link have their
# respective attribute populated — a missing back-link is not a
# DDF00023 failure (it's a different rule's concern).
from usdm4.rules.rule_template import RuleTemplate


SCOPE_CLASSES = [
    "Activity",
    "EligibilityCriterion",
    "Encounter",
    "NarrativeContent",
    "StudyEpoch",
]


class RuleDDF00023(RuleTemplate):
    """
    DDF00023: To ensure consistent ordering, when both previous and next attributes are available within an entity the previous id value must match the next id value of the referred instance.

    Applies to: Activity, EligibilityCriterion, Encounter, NarrativeContent, StudyEpoch
    Attributes: previousId, nextId
    """

    def __init__(self):
        super().__init__(
            "DDF00023",
            RuleTemplate.ERROR,
            "To ensure consistent ordering, when both previous and next attributes are available within an entity the previous id value must match the next id value of the referred instance.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in SCOPE_CLASSES:
            for instance in data.instances_by_klass(klass):
                self_id = instance.get("id")
                prev_id = instance.get("previousId")
                next_id = instance.get("nextId")
                if prev_id:
                    prev = data.instance_by_id(prev_id)
                    if isinstance(prev, dict) and prev.get("nextId"):
                        if prev["nextId"] != self_id:
                            self._add_failure(
                                f"{klass}.previousId points at {prev_id!r} but that instance's nextId is {prev['nextId']!r} (expected {self_id!r})",
                                klass,
                                "previousId, nextId",
                                data.path_by_id(self_id),
                            )
                if next_id:
                    nxt = data.instance_by_id(next_id)
                    if isinstance(nxt, dict) and nxt.get("previousId"):
                        if nxt["previousId"] != self_id:
                            self._add_failure(
                                f"{klass}.nextId points at {next_id!r} but that instance's previousId is {nxt['previousId']!r} (expected {self_id!r})",
                                klass,
                                "previousId, nextId",
                                data.path_by_id(self_id),
                            )
        return self._result()
