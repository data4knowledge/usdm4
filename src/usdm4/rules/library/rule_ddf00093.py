# MANUAL: do not regenerate
#
# Within each StudyVersion.dateValues, the (type.code, frozenset of
# geographicScopes.type.code) tuple must be unique. Geographic scopes
# are sorted/frozen so {Global} vs {Global} compares equal regardless
# of ordering. Twin of DDF00181 (StudyDefinitionDocumentVersion).
from collections import defaultdict

from usdm4.rules.rule_template import RuleTemplate


def _date_key(date):
    type_code = (
        (date.get("type") or {}).get("code")
        if isinstance(date.get("type"), dict)
        else None
    )
    scopes = date.get("geographicScopes") or []
    scope_codes = frozenset(
        (s.get("type") or {}).get("code")
        for s in scopes
        if isinstance(s, dict) and isinstance(s.get("type"), dict)
    )
    return (type_code, scope_codes)


class RuleDDF00093(RuleTemplate):
    """
    DDF00093: Date values associated to a study version must be unique regarding the combination of type and geographic scopes of the date.

    Applies to: StudyVersion
    Attributes: dateValues
    """

    def __init__(self):
        super().__init__(
            "DDF00093",
            RuleTemplate.ERROR,
            "Date values associated to a study version must be unique regarding the combination of type and geographic scopes of the date.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sv in data.instances_by_klass("StudyVersion"):
            groups: dict = defaultdict(list)
            for date in sv.get("dateValues") or []:
                if not isinstance(date, dict):
                    continue
                key = _date_key(date)
                if key[0] is None:
                    continue
                groups[key].append(date)
            for key, dates in groups.items():
                if len(dates) <= 1:
                    continue
                for date in dates:
                    self._add_failure(
                        f"StudyVersion.dateValues has {len(dates)} entries with type.code {key[0]!r} and geographic scopes {sorted(key[1])}",
                        "GovernanceDate",
                        "type, geographicScopes",
                        data.path_by_id(date["id"]),
                    )
        return self._result()
