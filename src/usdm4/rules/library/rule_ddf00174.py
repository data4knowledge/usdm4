# MANUAL: do not regenerate
#
# Group StudyIdentifier by scopeId (the identified organization). More
# than one StudyIdentifier pointing at the same organization is a
# warning. Reports against each offending StudyIdentifier.
from collections import defaultdict

from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00174(RuleTemplate):
    """
    DDF00174: An identified organization is not expected to have more than 1 identifier for the study.

    Applies to: StudyIdentifier
    Attributes: scopeId
    """

    def __init__(self):
        super().__init__(
            "DDF00174",
            RuleTemplate.WARNING,
            "An identified organization is not expected to have more than 1 identifier for the study.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        by_scope: dict = defaultdict(list)
        for identifier in data.instances_by_klass("StudyIdentifier"):
            scope_id = identifier.get("scopeId")
            if scope_id:
                by_scope[scope_id].append(identifier)
        for scope_id, identifiers in by_scope.items():
            if len(identifiers) <= 1:
                continue
            for identifier in identifiers:
                self._add_failure(
                    f"Organization {scope_id!r} has {len(identifiers)} StudyIdentifiers",
                    "StudyIdentifier",
                    "scopeId",
                    data.path_by_id(identifier["id"]),
                )
        return self._result()
