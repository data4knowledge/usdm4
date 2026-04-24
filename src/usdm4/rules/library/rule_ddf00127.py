# MANUAL: do not regenerate
#
# Encounter.scheduledAtId points to a Timing. That Timing must be
# defined under the same StudyDesign as the Encounter. Sister of
# DDF00107 (SAI sub-timeline same design).
from usdm4.rules.rule_template import RuleTemplate


STUDY_DESIGN_KLASSES = ["StudyDesign", "InterventionalStudyDesign", "ObservationalStudyDesign"]


class RuleDDF00127(RuleTemplate):
    """
    DDF00127: An encounter must only be scheduled at a timing that is defined within the same study design as the encounter.

    Applies to: Encounter
    Attributes: scheduledAtId
    """

    def __init__(self):
        super().__init__(
            "DDF00127",
            RuleTemplate.ERROR,
            "An encounter must only be scheduled at a timing that is defined within the same study design as the encounter.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for encounter in data.instances_by_klass("Encounter"):
            timing_id = encounter.get("scheduledAtId")
            if not timing_id:
                continue
            timing = data.instance_by_id(timing_id)
            if not isinstance(timing, dict):
                continue
            enc_design = data.parent_by_klass(encounter.get("id"), STUDY_DESIGN_KLASSES)
            timing_design = data.parent_by_klass(timing_id, STUDY_DESIGN_KLASSES)
            if enc_design is None or timing_design is None:
                continue
            if enc_design.get("id") != timing_design.get("id"):
                self._add_failure(
                    f"Encounter.scheduledAtId {timing_id!r} resolves to a Timing in a different StudyDesign",
                    "Encounter",
                    "scheduledAtId",
                    data.path_by_id(encounter["id"]),
                )
        return self._result()
