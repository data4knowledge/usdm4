# MANUAL: do not regenerate
#
# Within a set of siblings of the same class under the same parent
# instance, no two siblings can share a non-null previousId, and no
# two can share a non-null nextId. CORE's `is_not_unique_set` keys
# the sibling set by (parent_entity, parent_id, parent_rel) — we
# use (parent_id, instance class) as the proxy since DataStore's
# `_parent` gives us the parent directly, and the instance's class
# stands in for parent_rel (in practice each class lives in one
# named list per parent).
from collections import defaultdict

from usdm4.rules.rule_template import RuleTemplate


SCOPE_CLASSES = [
    "Activity",
    "EligibilityCriterion",
    "Encounter",
    "NarrativeContent",
    "StudyEpoch",
]


class RuleDDF00027(RuleTemplate):
    """
    DDF00027: To ensure consistent ordering, the same instance must not be referenced more than once as previous or next.

    Applies to: Activity, EligibilityCriterion, Encounter, NarrativeContent, StudyEpoch
    Attributes: previousId, nextId
    """

    def __init__(self):
        super().__init__(
            "DDF00027",
            RuleTemplate.ERROR,
            "To ensure consistent ordering, the same instance must not be referenced more than once as previous or next.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        # Group (parent_id, klass) -> {"prev": [(instance, target_id)...], "next": [...]}
        groups: dict = defaultdict(lambda: {"prev": [], "next": []})
        for klass in SCOPE_CLASSES:
            for instance in data.instances_by_klass(klass):
                parent = data._parent.get(instance.get("id"))
                if not isinstance(parent, dict):
                    continue
                key = (parent.get("id"), klass)
                prev_id = instance.get("previousId")
                next_id = instance.get("nextId")
                if prev_id:
                    groups[key]["prev"].append((instance, prev_id))
                if next_id:
                    groups[key]["next"].append((instance, next_id))
        for (parent_id, klass), links in groups.items():
            for attr in ("prev", "next"):
                counts: dict = defaultdict(list)
                for instance, target_id in links[attr]:
                    counts[target_id].append(instance)
                for target_id, instances in counts.items():
                    if len(instances) <= 1:
                        continue
                    attr_name = "previousId" if attr == "prev" else "nextId"
                    for instance in instances:
                        self._add_failure(
                            f"{klass}.{attr_name} {target_id!r} is referenced by {len(instances)} siblings under the same parent",
                            klass,
                            attr_name,
                            data.path_by_id(instance["id"]),
                        )
        return self._result()
