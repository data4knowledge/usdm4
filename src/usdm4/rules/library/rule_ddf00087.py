from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00087(RuleTemplate):
    """
    DDF00087: Encounter ordering using previous and next attributes is expected to be consistent with the order of corresponding scheduled activity instances according to their specified default conditions.

    Applies to: Encounter
    Attributes: previous, next
    """

    def __init__(self):
        super().__init__(
            "DDF00087",
            RuleTemplate.WARNING,
            "Encounter ordering using previous and next attributes is expected to be consistent with the order of corresponding scheduled activity instances according to their specified default conditions.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.study.versions)@$sv.
    #         ($sv.studyDesigns)@$sd.
    #             ($sd.scheduleTimelines[mainTimeline = true])@$st.
    #                 (
    #                     $actord := $utils.parse_refs("nextId","next",$sd.encounters)
    #                                 [previousId = null].$append(id,**.next.id);
    #                     $reford := $utils.parse_refs("defaultConditionId","defaultCondition",$st.instances)
    #                                 [id = $st.entryId].**[instanceType="ScheduledActivityInstance" and encounterId in $sd.encounters.id].encounterId
    #                                 ~> $filter(function($v,$i,$a){$i = 0 or ($i > 0 and $v != $a[$i-1])});
    #                     $encounter := function($id){($e:=$sd.encounters[id=$id];$id & ": " & $e.name)};
    #                     {
    #                         "instanceType": $sd.instanceType,
    #                         "id": $sd.id,
    #                         "path": $sd._path,
    #                         "name": $sd.name,
    #                         "ScheduleTimeline.id": $st.id,
    #                         "ScheduleTimeline.name": $st.name,
    #                         "ScheduleTimeline.mainTimeline": $st.mainTimeline,
    #                         "Encounter order by previous/next": "[ "&($actord ~> $map($encounter) ~> $join(" > "))&" ]",
    #                         "Encounter order by timeline refs": "[ "&($reford ~> $map($encounter) ~> $join(" > "))&" ]"
    #                     }[`Encounter order by previous/next` != `Encounter order by timeline refs`]
    #                 )

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00087: not yet implemented")
