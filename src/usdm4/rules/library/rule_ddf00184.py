# MANUAL: do not regenerate
#
# Self-reference check: a Substance must not name itself as its
# reference substance (`referenceSubstanceId` is a scalar FK in USDM JSON).
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00184(RuleTemplate):
    """
    DDF00184: A substance must not references itself as a reference substance.

    Applies to: Substance
    Attributes: referenceSubstanceId
    """

    def __init__(self):
        super().__init__(
            "DDF00184",
            RuleTemplate.ERROR,
            "A substance must not references itself as a reference substance.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for substance in data.instances_by_klass("Substance"):
            ref_id = substance.get("referenceSubstanceId")
            if ref_id and ref_id == substance.get("id"):
                self._add_failure(
                    "Substance refers to itself as its reference substance",
                    "Substance",
                    "referenceSubstanceId",
                    data.path_by_id(substance["id"]),
                )
        return self._result()
