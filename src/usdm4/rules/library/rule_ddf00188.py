# MANUAL: do not regenerate
#
# plannedSex must be a subset of {Male C20197, Female C16576} with no
# duplicates — i.e., the allowed code-sets are {Male}, {Female}, or
# {Male, Female}. CORE encodes this as "count(ids) != count(distinct(codes))
# OR any code not in [C16576, C20197]".
from usdm4.rules.rule_template import RuleTemplate


MALE_CODE = "C20197"
FEMALE_CODE = "C16576"
ALLOWED_CODES = {MALE_CODE, FEMALE_CODE}
SCOPE_CLASSES = ["StudyDesignPopulation", "StudyCohort"]


class RuleDDF00188(RuleTemplate):
    """
    DDF00188: A planned sex must ether include a single entry of male or female or both female and male as entries.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: plannedSex
    """

    def __init__(self):
        super().__init__(
            "DDF00188",
            RuleTemplate.ERROR,
            "A planned sex must ether include a single entry of male or female or both female and male as entries.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in SCOPE_CLASSES:
            for instance in data.instances_by_klass(klass):
                planned_sex = instance.get("plannedSex") or []
                if not planned_sex:
                    continue  # absence handled by separate required/CT rules
                codes = [
                    entry.get("code")
                    for entry in planned_sex
                    if isinstance(entry, dict)
                ]
                # Duplicate entries (same code more than once)
                if len(codes) != len(set(codes)):
                    self._add_failure(
                        f"{klass}.plannedSex has duplicate entries",
                        klass,
                        "plannedSex",
                        data.path_by_id(instance["id"]),
                    )
                    continue
                # Any unexpected code (not male/female)
                if any(code not in ALLOWED_CODES for code in codes):
                    self._add_failure(
                        f"{klass}.plannedSex contains a code other than Male (C20197) or Female (C16576)",
                        klass,
                        "plannedSex",
                        data.path_by_id(instance["id"]),
                    )
        return self._result()
