# MANUAL: do not regenerate
#
# Twin of DDF00238 but for Strength.denominator. CORE condition:
#   $exists(denominator.id) and (!$exists(denominator.unit) or unit=null)
# i.e. denominator is "specified" when it has an id; once specified, its
# unit attribute must be non-empty.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00186(RuleTemplate):
    """
    DDF00186: If a strength denominator is specified, it must have a unit.

    Applies to: Strength
    Attributes: denominator
    """

    def __init__(self):
        super().__init__(
            "DDF00186",
            RuleTemplate.ERROR,
            "If a strength denominator is specified, it must have a unit.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for strength in data.instances_by_klass("Strength"):
            denominator = strength.get("denominator")
            if not isinstance(denominator, dict):
                continue
            # "specified" per CORE = has an id
            if not denominator.get("id"):
                continue
            if not denominator.get("unit"):
                self._add_failure(
                    "Strength.denominator is specified but has no unit",
                    "Strength",
                    "denominator",
                    data.path_by_id(strength["id"]),
                )
        return self._result()
