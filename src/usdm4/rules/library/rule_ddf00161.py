# MANUAL: do not regenerate
#
# prev/next on Activity defines the display walk (preorder) of the
# activity tree — a parent row is followed by its whole subtree, then
# the next parent, etc. Three sub-checks mirror CORE's three Issue
# predicates:
#
#   1. If an Activity has childIds, its own nextId must be one of
#      those childIds (stepping into the first child of the subtree).
#   2. If an Activity is a child (some parent has it in childIds),
#      its previousId must be within { parent.id, OTHER children of
#      that parent, and their deep descendants } for at least one of
#      its parents. Multi-parent activities satisfy the check if the
#      previousId is allowed under ANY parent's context (matches the
#      flattening CORE's JSONata does via `$pacts[...].[id,...].*`).
#   3. If an Activity's previousId resolves to an Activity with
#      childIds, this Activity must be one of those childIds.
#      (Reverse of Issue 1: caught from the child's perspective.)
from collections import defaultdict

from usdm4.rules.rule_template import RuleTemplate


STUDY_DESIGN_KLASSES = [
    "StudyDesign",
    "InterventionalStudyDesign",
    "ObservationalStudyDesign",
]


def _descendants(activity_id, children_map, visited=None):
    """All ids in the subtree rooted at activity_id, not including the root."""
    visited = visited if visited is not None else set()
    out: set = set()
    for child in children_map.get(activity_id) or []:
        if child in visited:
            continue
        visited.add(child)
        out.add(child)
        out.update(_descendants(child, children_map, visited))
    return out


class RuleDDF00161(RuleTemplate):
    """
    DDF00161: The ordering of activities (using the previous and next attributes) must include the parents (e.g. activities referring to children) preceding their children.

    Applies to: Activity
    Attributes: previousId, nextId
    """

    def __init__(self):
        super().__init__(
            "DDF00161",
            RuleTemplate.ERROR,
            "The ordering of activities (using the previous and next attributes) must include the parents (e.g. activities referring to children) preceding their children.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in STUDY_DESIGN_KLASSES:
            for design in data.instances_by_klass(klass):
                activities = [
                    a
                    for a in design.get("activities") or []
                    if isinstance(a, dict) and a.get("id")
                ]
                if not activities:
                    continue
                by_id = {a["id"]: a for a in activities}
                # parent -> list of child ids, and child -> list of parent ids
                # (an Activity can appear in childIds of multiple parents —
                # e.g. shared activities across different branches).
                children_map = {
                    a["id"]: list(a.get("childIds") or []) for a in activities
                }
                parents_of: dict = defaultdict(list)
                for parent_id, child_ids in children_map.items():
                    for cid in child_ids:
                        parents_of[cid].append(parent_id)

                for activity in activities:
                    aid = activity["id"]
                    child_ids = activity.get("childIds") or []
                    prev_id = activity.get("previousId")
                    next_id = activity.get("nextId")

                    # Issue 1 — parent must step into a child via nextId
                    if child_ids and next_id not in child_ids:
                        self._add_failure(
                            f"Activity {aid!r} has childIds but its nextId {next_id!r} is not one of them",
                            "Activity",
                            "nextId, childIds",
                            data.path_by_id(aid),
                        )

                    # Issue 2 — child's previousId must be in the allowed set
                    # for AT LEAST one of its parents.
                    parent_list = parents_of.get(aid) or []
                    if parent_list:
                        allowed: set = set()
                        for parent_id in parent_list:
                            allowed.add(parent_id)
                            # Siblings + their deep descendants, excluding self.
                            allowed |= _descendants(parent_id, children_map)
                        allowed.discard(aid)
                        if prev_id not in allowed:
                            parents_str = (
                                parent_list[0]
                                if len(parent_list) == 1
                                else f"parents {parent_list!r}"
                            )
                            self._add_failure(
                                f"Activity {aid!r} is a child of {parents_str} "
                                f"but its previousId {prev_id!r} is neither a "
                                f"parent nor another descendant of a parent",
                                "Activity",
                                "previousId",
                                data.path_by_id(aid),
                            )

                    # Issue 3 — if previousId is a parent (has children), we
                    # must be one of them.
                    if prev_id and prev_id in by_id:
                        prev_children = children_map.get(prev_id) or []
                        if prev_children and aid not in prev_children:
                            self._add_failure(
                                f"Activity {aid!r} has previousId {prev_id!r} which has its own childIds, but {aid!r} is not one of them",
                                "Activity",
                                "previousId",
                                data.path_by_id(aid),
                            )
        return self._result()
