# MANUAL: do not regenerate
#
# Anchor on StudyDesignPopulation / StudyCohort and pull their
# `plannedAge` — which is a Range. Flag the Range when it has
# `isApproximate = True`. The YAML's `class: Range` is too broad;
# scoping via the parent class avoids flagging unrelated Range instances
# (e.g. under duration, strength, etc.).
from usdm4.rules.rule_template import RuleTemplate


SCOPE_CLASSES = ["StudyDesignPopulation", "StudyCohort"]


class RuleDDF00042(RuleTemplate):
    """
    DDF00042: The range specified for a planned age is not expected to be approximate.

    Applies to: Range (under StudyDesignPopulation.plannedAge / StudyCohort.plannedAge)
    Attributes: isApproximate
    """

    def __init__(self):
        super().__init__(
            "DDF00042",
            RuleTemplate.WARNING,
            "The range specified for a planned age is not expected to be approximate.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in SCOPE_CLASSES:
            for instance in data.instances_by_klass(klass):
                age = instance.get("plannedAge")
                if not isinstance(age, dict):
                    continue
                if age.get("isApproximate") is True:
                    self._add_failure(
                        f"{klass}.plannedAge is marked as approximate",
                        "Range",
                        "isApproximate",
                        data.path_by_id(age["id"])
                        if age.get("id")
                        else data.path_by_id(instance["id"]),
                    )
        return self._result()
