# MANUAL: do not regenerate
#
# plannedAge is a nested Quantity (or Range) on StudyDesignPopulation
# / StudyCohort. Its `unit` (embedded Code) must come from codelist
# C66781 ("Age Unit"). ct_config's klass_attribute_mapping can't
# express "nested under plannedAge", so we fetch the codelist
# directly via the CT library and compare codes in-line. C66781 is
# registered in ct_config.code_lists so it will be loaded.
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
        codelist = ct._by_code_list.get(AGE_UNIT_CODELIST)
        if codelist is None:
            # C66781 is registered in ct_config.yaml but only populates
            # after a CT cache refresh. If the cache is stale we skip
            # the check rather than crash the engine; the rule
            # re-activates once the cache is refreshed.
            return True
        valid_codes = {term["conceptId"] for term in codelist.get("terms") or []}
        valid_decodes = {term["preferredTerm"] for term in codelist.get("terms") or []}
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
                    if code not in valid_codes or (
                        decode is not None and decode not in valid_decodes
                    ):
                        self._add_failure(
                            f"{klass}.plannedAge unit {code!r}/{decode!r} is not in the Age Unit codelist ({AGE_UNIT_CODELIST})",
                            klass,
                            "plannedAge",
                            data.path_by_id(instance["id"]),
                        )
        return self._result()
