# MANUAL: do not regenerate
#
# Id values must not contain spaces. Applies to every indexed instance —
# DataStore's private `_ids` dict is the only way to reach all of them
# without enumerating every class. Acceptable here because it's a
# cross-cutting model-wide check.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00260(RuleTemplate):
    """
    DDF00260: Id values are expected not to have spaces in their string values.

    Applies to: All
    Attributes: id
    """

    def __init__(self):
        super().__init__(
            "DDF00260",
            RuleTemplate.WARNING,
            "Id values are expected not to have spaces in their string values.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        # Iterate every indexed instance. DataStore doesn't expose a public
        # iterator, so access _ids directly.
        for iid, item in data._ids.items():
            if not isinstance(iid, str) or " " not in iid:
                continue
            instance_type = (
                item.get("instanceType", "Unknown")
                if isinstance(item, dict)
                else "Unknown"
            )
            self._add_failure(
                f"id value {iid!r} contains a space",
                instance_type,
                "id",
                data.path_by_id(iid),
            )
        return self._result()
