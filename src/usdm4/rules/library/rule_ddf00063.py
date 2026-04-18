# MANUAL: do not regenerate
#
# Per CORE conditions: for each AliasCode, if any alias in
# standardCodeAliases shares codeSystem + codeSystemVersion
# (case-insensitive) with the standardCode AND shares either code or
# decode (also case-insensitive), that's a failure.
from usdm4.rules.rule_template import RuleTemplate


def _lower(value):
    return value.lower() if isinstance(value, str) else value


class RuleDDF00063(RuleTemplate):
    """
    DDF00063: A standard code alias is not expected to be equal to the standard code (e.g. no equal code or decode for the same coding system version is expected).

    Applies to: AliasCode
    Attributes: standardCodeAliases
    """

    def __init__(self):
        super().__init__(
            "DDF00063",
            RuleTemplate.WARNING,
            "A standard code alias is not expected to be equal to the standard code (e.g. no equal code or decode for the same coding system version is expected).",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for alias_code in data.instances_by_klass("AliasCode"):
            standard = alias_code.get("standardCode")
            aliases = alias_code.get("standardCodeAliases") or []
            if not isinstance(standard, dict) or not aliases:
                continue
            s_system = _lower(standard.get("codeSystem"))
            s_version = _lower(standard.get("codeSystemVersion"))
            s_code = _lower(standard.get("code"))
            s_decode = _lower(standard.get("decode"))
            for alias in aliases:
                if not isinstance(alias, dict):
                    continue
                if _lower(alias.get("codeSystem")) != s_system:
                    continue
                if _lower(alias.get("codeSystemVersion")) != s_version:
                    continue
                a_code = _lower(alias.get("code"))
                a_decode = _lower(alias.get("decode"))
                if (s_code is not None and a_code == s_code) or (
                    s_decode is not None and a_decode == s_decode
                ):
                    self._add_failure(
                        "AliasCode has a standardCodeAlias equal to the standardCode (same code or decode within the same coding system/version)",
                        "AliasCode",
                        "standardCodeAliases",
                        data.path_by_id(alias_code["id"]),
                    )
                    break  # one report per AliasCode is enough
        return self._result()
