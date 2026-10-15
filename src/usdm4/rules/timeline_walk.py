"""The main timeline walked in its default order — shared by the encounter
and epoch order rules, DDF00087 and DDF00088 (issue 89).

A walk starts at the timeline's entry and follows ``defaultConditionId``
through activity AND decision instances. A decision whose default leads
back to an instance already walked is a loop (a repeating visit): the walk
leaves it by its first condition assignment not yet walked, so the visits
after the loop are reached. Revisiting an instance any other way is a cycle.
"""


def walk_main_timeline(timeline: dict) -> tuple[list[dict], bool]:
    """The ScheduledActivityInstances met on the walk, in order, and whether
    a cycle was found."""
    instances = [i for i in timeline.get("instances") or [] if isinstance(i, dict)]
    by_id = {i.get("id"): i for i in instances if i.get("id")}
    visited: set = set()
    walked: list[dict] = []
    current = timeline.get("entryId")
    while current and current in by_id:
        if current in visited:
            return walked, True
        visited.add(current)
        node = by_id[current]
        following = node.get("defaultConditionId")
        if node.get("instanceType") == "ScheduledDecisionInstance":
            if following is None or following in visited:
                forward = [
                    c.get("conditionTargetId")
                    for c in node.get("conditionAssignments") or []
                    if isinstance(c, dict)
                    and c.get("conditionTargetId")
                    and c.get("conditionTargetId") not in visited
                ]
                following = forward[0] if forward else None
        elif node.get("instanceType") == "ScheduledActivityInstance":
            walked.append(node)
        current = following
    return walked, False


def first_occurrences(ids: list) -> list:
    """Each id once, in the order first met."""
    seen: set = set()
    out = []
    for item in ids:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
