# MANUAL: do not regenerate
#
# One-step chain check: if Substance X names Substance Y as its reference
# substance, then Y itself must NOT carry its own referenceSubstanceId. This
# prevents a reference-substance from also being a reference to yet another
# substance. The CORE JSONata walks products→ingredients→substance and
# filters where the parent substance's referenceSubstance has a non-empty
# referenceSubstance of its own; implemented here as an O(n) lookup over
# all Substances using the datastore.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00253(RuleTemplate):
    """
    DDF00253: A reference substance must not have a reference substance.

    Applies to: Substance
    Attributes: referenceSubstanceId
    """

    def __init__(self):
        super().__init__(
            "DDF00253",
            RuleTemplate.ERROR,
            "A reference substance must not have a reference substance.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        # Collect the set of Substance ids that are themselves referenced as
        # another substance's reference substance — these are the "reference
        # substances" the rule talks about. For any such reference-substance,
        # it must not have a referenceSubstanceId of its own.
        ref_ids = set()
        for substance in data.instances_by_klass("Substance"):
            ref_id = substance.get("referenceSubstanceId")
            if ref_id:
                ref_ids.add(ref_id)
        for substance in data.instances_by_klass("Substance"):
            if substance.get("id") in ref_ids and substance.get("referenceSubstanceId"):
                self._add_failure(
                    "Substance is referenced as a reference substance but itself has a reference substance",
                    "Substance",
                    "referenceSubstanceId",
                    data.path_by_id(substance["id"]),
                )
        return self._result()
