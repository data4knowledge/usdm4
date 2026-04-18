from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00244(RuleTemplate):
    """
    DDF00244: Referenced items in the narrative content item texts must be available elsewhere in the data model.

    Applies to: NarrativeContentItem
    Attributes: text
    """

    def __init__(self):
        super().__init__(
            "DDF00244",
            RuleTemplate.ERROR,
            "Referenced items in the narrative content item texts must be available elsewhere in the data model.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (
    #       $lkp:=**[id and instanceType].$each(function($v,$k){{$join([instanceType,id,$k],"|"):$v}})~>$merge;
    #       ($.study.versions.narrativeContentItems[$type(text)="string" and $contains(text,/usdm:ref/)])@$nci.
    #         $match( $nci.text,
    #                 /<usdm:ref([^>]*)(\/>|><\/usdm:ref>)/
    #         )@$ref.
    #         (
    #           $g0_or_null := function($m){$m ? $m.groups[0] : ""};
    #           {
    #             "instanceType": $nci.instanceType,
    #             "id": $nci.id,
    #             "path": $nci._path,                     
    #             "name": $nci.name,
    #             "text": $nci.text,
    #             "usdm_ref": {
    #                           "match": $ref.match,
    #                           "klass": $match($ref.groups[0],/klass=\"([a-zA-Z]+)\"/) ~> $g0_or_null(),
    #                           "id": $match($ref.groups[0],/id=\"(\w+)\"/) ~> $g0_or_null(),
    #                           "attribute": $match($ref.groups[0],/attribute=\"([a-zA-Z]+)\"/) ~> $g0_or_null()
    #                         }
    #           }
    #         )
    #         ~>  $map(function($v)
    #               {
    #                 (
    #                   $ref_val := "usdm_ref" in $keys($v)
    #                               ? (
    #                                   $k := $join([$v.usdm_ref.klass,$v.usdm_ref.id,$v.usdm_ref.attribute],"|");
    #                                   $k in $keys($lkp)
    #                                   ? $lookup($lkp,$k)
    #                                   : "!!NOT FOUND!!"
    #                                 )
    #                               : $v.value;
    #                   $v ~> |$|{"Invalid Reference": $v.usdm_ref.match, "Referenced Value": $ref_val},['usdm_ref']|
    #                 )
    #               }
    #             )
    #         ~>  $filter(function($v)
    #               {
    #                 $v.`Referenced Value` = "!!NOT FOUND!!"
    #               }
    #             )
    #     )

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00244: not yet implemented")
