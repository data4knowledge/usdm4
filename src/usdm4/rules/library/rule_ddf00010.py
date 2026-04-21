# MANUAL: do not regenerate
#
# CORE's JSONata groups every instance with {id, instanceType, name} by
# instanceType then by name, and flags groups with count > 1. That is
# "names unique per class, model-wide" — stricter than the rule text's
# "same parent class" phrasing but matching the authoritative check.
# Iterates via DataStore._ids to avoid having to enumerate every class.
from collections import defaultdict

from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00010(RuleTemplate):
    """
    DDF00010: The names of all child instances of the same parent class must be unique.

    Applies to: All classes carrying a `name` attribute
    Attributes: name
    """

    def __init__(self):
        super().__init__(
            "DDF00010",
            RuleTemplate.ERROR,
            "The names of all child instances of the same parent class must be unique.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        # Group (instanceType, name) across every indexed instance with a name.
        groups: dict = defaultdict(list)
        for iid, instance in data._ids.items():
            if not isinstance(instance, dict):
                continue
            name = instance.get("name")
            itype = instance.get("instanceType")
            if not (isinstance(name, str) and name and itype):
                continue
            groups[(itype, name)].append(instance)
        for (itype, name), instances in groups.items():
            if len(instances) <= 1:
                continue
            for instance in instances:
                self._add_failure(
                    f"{itype} name {name!r} is not unique ({len(instances)} occurrences)",
                    itype,
                    "name",
                    data.path_by_id(instance["id"]),
                )
        return self._result()
