# MANUAL: do not regenerate
#
# plannedAge is a nested Quantity (or Range) on StudyDesignPopulation
# / StudyCohort. Its `unit` (embedded Code) must come from codelist
# C66781 ("Age Unit"). ct_config's klass_attribute_mapping can't
# express "nested under plannedAge", so we route the membership check
# through the common Library predicate (`is_in_codelist`) — same seam
# every CT-checking rule uses, so extensions to C66781 (if any are ever
# loaded) are honoured transparently.
#
# Missing-codelist contract: if C66781 is not loaded, the Library
# predicate raises MissingCodelistError. We let it propagate; the rule
# engine surfaces it as a per-rule EXCEPTION outcome so the operator
# sees the config flaw rather than a misleading "rule passed". See
# feedback_missing_codelist_must_raise.
from usdm4.rules.rule_template import RuleTemplate


SCOPE_CLASSES = ["StudyDesignPopulation", "StudyCohort"]
AGE_UNIT_CODELIST = "C66781"


def _iter_quantities(planned_age):
    """Yield each Quantity-shaped endpoint under plannedAge (Quantity OR Range)."""
    if not isinstance(planned_age, dict):
        return
    # Quantity shape: has 'value'
    if "value" in planned_age:
        yield planned_age
        return
    # Range shape: has 'minValue' / 'maxValue'
    for endpoint_name in ("minValue", "maxValue"):
        endpoint = planned_age.get(endpoint_name)
        if isinstance(endpoint, dict):
            yield endpoint


class RuleDDF00237(RuleTemplate):
    """
    DDF00237: The unit of a planned age is expected to be specified using terms from the Age Unit (C66781) SDTM codelist.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: plannedAge (nested unit)
    """

    def __init__(self):
        super().__init__(
            "DDF00237",
            RuleTemplate.ERROR,
            "The unit of a planned age is expected to be specified using terms from the Age Unit (C66781) SDTM codelist.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        ct = config["ct"]
        # No cache-stale guard here: if C66781 isn't loaded, the first
        # is_in_codelist call raises MissingCodelistError and the rule
        # engine logs it as an exception outcome. That's the right
        # signal — a missing baseline codelist is a config flaw, not a
        # per-document finding.
        for klass in SCOPE_CLASSES:
            for instance in data.instances_by_klass(klass):
                planned_age = instance.get("plannedAge")
                for quantity in _iter_quantities(planned_age):
                    unit = quantity.get("unit")
                    if not isinstance(unit, dict):
                        continue  # unit absent; separate concern
                    standard = unit.get("standardCode")
                    if not isinstance(standard, dict):
                        self._add_failure(
                            f"{klass}.plannedAge has a unit with no standardCode",
                            klass,
                            "plannedAge",
                            data.path_by_id(instance["id"]),
                        )
                        continue
                    code = standard.get("code")
                    decode = standard.get("decode")
                    if code is None or not ct.is_in_codelist(
                        code, AGE_UNIT_CODELIST, by="concept_id"
                    ):
                        self._add_failure(
                            f"{klass}.plannedAge unit {code!r}/{decode!r} is not in the Age Unit codelist ({AGE_UNIT_CODELIST})",
                            klass,
                            "plannedAge",
                            data.path_by_id(instance["id"]),
                        )
                        continue
                    if decode is not None and not ct.is_in_codelist(
                        decode, AGE_UNIT_CODELIST, by="any"
                    ):
                        self._add_failure(
                            f"{klass}.plannedAge unit {code!r}/{decode!r} is not in the Age Unit codelist ({AGE_UNIT_CODELIST})",
                            klass,
                            "plannedAge",
                            data.path_by_id(instance["id"]),
                        )
        return self._result()
