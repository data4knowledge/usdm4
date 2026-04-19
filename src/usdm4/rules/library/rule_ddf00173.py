# MANUAL: do not regenerate
#
# Identifier text must be unique within (scopeId, instanceType). Four
# identifier classes carry a scopeId + text pair. CORE groups by
# text|scopeId|instanceType and flags groups with count > 1. We report
# against every offending instance so the user sees all duplicates.
from collections import defaultdict

from usdm4.rules.rule_template import RuleTemplate


SCOPE_CLASSES = [
    "StudyIdentifier",
    "ReferenceIdentifier",
    "AdministrableProductIdentifier",
    "MedicalDeviceIdentifier",
]


class RuleDDF00173(RuleTemplate):
    """
    DDF00173: Every identifier must be unique within the scope of an identified organization.

    Applies to: StudyIdentifier, ReferenceIdentifier, AdministrableProductIdentifier, MedicalDeviceIdentifier
    Attributes: text, scopeId
    """

    def __init__(self):
        super().__init__(
            "DDF00173",
            RuleTemplate.ERROR,
            "Every identifier must be unique within the scope of an identified organization.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        groups: dict = defaultdict(list)
        for klass in SCOPE_CLASSES:
            for identifier in data.instances_by_klass(klass):
                scope_id = identifier.get("scopeId")
                text = identifier.get("text")
                if scope_id is None or text is None:
                    continue
                key = (klass, scope_id, text)
                groups[key].append(identifier)
        for (klass, scope_id, text), identifiers in groups.items():
            if len(identifiers) <= 1:
                continue
            for identifier in identifiers:
                self._add_failure(
                    f"{klass} text {text!r} is not unique within scope {scope_id!r} ({len(identifiers)} occurrences)",
                    klass,
                    "text, scopeId",
                    data.path_by_id(identifier["id"]),
                )
        return self._result()
