from usdm4.rules.rule_template import RuleTemplate


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

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     $.study.versions.studyDesigns.
    #       {
    #           "instanceType": instanceType,
    #           "id": id,
    #           "path": _path,
    #           "name": name,
    #           "# Main timelines": $count(scheduleTimelines[mainTimeline=true]),
    #           "Main timelines": scheduleTimelines[mainTimeline=true]
    #                             ~> $map(function($v){$v.id & ($v.name ? " [" & $v.name & "]")})
    #       }[`# Main timelines` != 1][]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00012: not yet implemented")
