from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00088(RuleTemplate):
    """
    DDF00088: Epoch ordering using previous and next attributes is expected to be consistent with the order of corresponding scheduled activity instances according to their specified default conditions.

    Applies to: StudyEpoch
    Attributes: previous, next
    """

    def __init__(self):
        super().__init__(
            "DDF00088",
            RuleTemplate.WARNING,
            "Epoch ordering using previous and next attributes is expected to be consistent with the order of corresponding scheduled activity instances according to their specified default conditions.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.study.versions)@$sv.
    #         ($sv.studyDesigns)@$sd.
    #             ($sd.scheduleTimelines[mainTimeline = true])@$st.
    #                 (
    #                     $actord := $utils.parse_refs("nextId","next",$sd.epochs)
    #                                 [previousId = null].$append(id,**.next.id);
    #                     $reford := $utils.parse_refs("defaultConditionId","defaultCondition",$st.instances)
    #                                 [id = $st.entryId].**[instanceType="ScheduledActivityInstance" and epochId in $sd.epochs.id].epochId
    #                                 ~> $filter(function($v,$i,$a){$i = 0 or ($i > 0 and $v != $a[$i-1])});
    #                     $epoch := function($id){($e:=$sd.epochs[id=$id];$id & ": " & $e.name)};
    #                     {
    #                         "instanceType": $sd.instanceType,
    #                         "id": $sd.id,
    #                         "path": $sd._path,
    #                         "name": $sd.name,
    #                         "ScheduleTimeline.id": $st.id,
    #                         "ScheduleTimeline.name": $st.name,
    #                         "ScheduleTimeline.mainTimeline": $st.mainTimeline,
    #                         "Epoch order by previous/next": "[ "&($actord ~> $map($epoch) ~> $join(" > "))&" ]",
    #                         "Epoch order by timeline refs": "[ "&($reford ~> $map($epoch) ~> $join(" > "))&" ]"
    #                     }[`Epoch order by previous/next` != `Epoch order by timeline refs`]
    #                 )

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00088: not yet implemented")
