from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00153(RuleTemplate):
    """
    DDF00153: A planned duration is expected for the main timeline.

    Applies to: ScheduleTimeline
    Attributes: plannedDuration
    """

    def __init__(self):
        super().__init__(
            "DDF00153",
            RuleTemplate.WARNING,
            "A planned duration is expected for the main timeline.",
        )

    # TODO: implement. MED_TEXT format: no specific format kind identified
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.versions.studyDesigns)@$sd.
    #       $sd.scheduleTimelines@$st.
    #       $st.
    #           [(  {
    #                   "instanceType": instanceType,
    #                   "id": id,
    #                   "path": _path,
    #                   "name": name,
    #                   "mainTimeline": mainTimeline,
    #                   "check":  mainTimeline=true and ($exists(plannedDuration)=false or plannedDuration=null)
    #               }
    #           )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00153: not yet implemented")
