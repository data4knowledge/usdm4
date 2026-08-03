# MANUAL: do not regenerate
#
# Twin of DDF00094 but scoped to StudyDefinitionDocumentVersion rather
# than StudyVersion. CORE's JSONata walks
# `study.documentedBy.versions.dateValues`.
from collections import defaultdict

from usdm4.rules.rule_template import RuleTemplate


GLOBAL_CODE = "C68846"


class RuleDDF00182(RuleTemplate):
    """
    DDF00182: Within a study protocol document version, if a date of a specific type exists with a global geographic scope then no other dates are expected with the same type.

    Applies to: StudyDefinitionDocumentVersion
    Attributes: dateValues
    """

    def __init__(self):
        super().__init__(
            "DDF00182",
            RuleTemplate.WARNING,
            "Within a study protocol document version, if a date of a specific type exists with a global geographic scope then no other dates are expected with the same type.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sddv in data.instances_by_klass("StudyDefinitionDocumentVersion"):
            date_values = sddv.get("dateValues") or []
            by_type: dict = defaultdict(list)
            types_with_global: set = set()
            for date in date_values:
                if not isinstance(date, dict):
                    continue
                type_code = (date.get("type") or {}).get("code")
                if not type_code:
                    continue
                by_type[type_code].append(date)
                if any(
                    (scope.get("type") or {}).get("code") == GLOBAL_CODE
                    for scope in (date.get("geographicScopes") or [])
                    if isinstance(scope, dict)
                ):
                    types_with_global.add(type_code)
            for type_code in types_with_global:
                dates = by_type[type_code]
                if len(dates) <= 1:
                    continue
                for date in dates:
                    self._add_failure(
                        f"Date of type.code {type_code!r} has a global geographic scope but {len(dates)} dates of that type exist in this document version",
                        "GovernanceDate",
                        "type, geographicScopes",
                        data.path_by_id(date["id"]),
                    )
        return self._result()
