# MANUAL: do not regenerate
#
# Cardinality rule: exactly one ScheduleTimeline per StudyDesign must have
# mainTimeline=True. CORE JSONata iterates studyDesigns and filters on
# scheduleTimelines[mainTimeline=true]. Implemented here via DataStore —
# iterate the concrete StudyDesign subclasses and access their embedded
# scheduleTimelines list directly.
from usdm4.rules.rule_template import RuleTemplate


STUDY_DESIGN_CLASSES = [
    "StudyDesign",
    "InterventionalStudyDesign",
    "ObservationalStudyDesign",
]


class RuleDDF00012(RuleTemplate):
    """
    DDF00012: Within a study design, there must be exactly one scheduled timeline which identifies as the main Timeline.

    Applies to: ScheduleTimeline
    Attributes: mainTimeline
    """

    def __init__(self):
        super().__init__(
            "DDF00012",
            RuleTemplate.ERROR,
            "Within a study design, there must be exactly one scheduled timeline which identifies as the main Timeline.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sd_cls in STUDY_DESIGN_CLASSES:
            for sd in data.instances_by_klass(sd_cls):
                count = sum(
                    1
                    for t in (sd.get("scheduleTimelines") or [])
                    if t.get("mainTimeline") is True
                )
                if count != 1:
                    self._add_failure(
                        f"Expected exactly one main ScheduleTimeline in study design, found {count}",
                        sd_cls,
                        "scheduleTimelines",
                        data.path_by_id(sd["id"]),
                    )
        return self._result()
