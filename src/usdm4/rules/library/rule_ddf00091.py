# MANUAL: do not regenerate
#
# FK-resolution check: every id in Condition.appliesToIds must
# resolve to an instance whose instanceType is one of the five
# allowed target classes. Pattern from DDF00114 / DDF00212.
from usdm4.rules.rule_template import RuleTemplate


ALLOWED_CLASSES = {
    "Procedure",
    "Activity",
    "BiomedicalConcept",
    "BiomedicalConceptCategory",
    "BiomedicalConceptSurrogate",
}


class RuleDDF00091(RuleTemplate):
    """
    DDF00091: When a condition applies to a procedure, activity, biomedical concept, biomedical concept category, or biomedical concept surrogate then an instance must be available in the corresponding class with the specified id.

    Applies to: Condition
    Attributes: appliesToIds
    """

    def __init__(self):
        super().__init__(
            "DDF00091",
            RuleTemplate.ERROR,
            "When a condition applies to a procedure, activity, biomedical concept, biomedical concept category, or biomedical concept surrogate then an instance must be available in the corresponding class with the specified id.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for condition in data.instances_by_klass("Condition"):
            for target_id in condition.get("appliesToIds") or []:
                if not target_id:
                    continue
                target = data.instance_by_id(target_id)
                target_type = target.get("instanceType") if isinstance(target, dict) else None
                if target_type not in ALLOWED_CLASSES:
                    reason = (
                        "does not resolve to any instance"
                        if target is None
                        else f"resolves to {target_type} (not one of {sorted(ALLOWED_CLASSES)})"
                    )
                    self._add_failure(
                        f"Condition.appliesToIds entry {target_id!r} {reason}",
                        "Condition",
                        "appliesToIds",
                        data.path_by_id(condition["id"]),
                    )
        return self._result()
