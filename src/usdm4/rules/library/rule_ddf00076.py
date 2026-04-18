from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00076(RuleTemplate):
    """
    DDF00076: If a biomedical concept is referenced from an activity then it is not expected to be referenced as well by a biomedical concept category that is referenced from the same activity.

    Applies to: Activity, BiomedicalConceptCategory
    Attributes: biomedicalConcepts, members
    """

    def __init__(self):
        super().__init__(
            "DDF00076",
            RuleTemplate.WARNING,
            "If a biomedical concept is referenced from an activity then it is not expected to be referenced as well by a biomedical concept category that is referenced from the same activity.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.study.versions)@$sv.
    #       [
    #         (
    #           $flatten:=function($tree) 
    #             {
    #               (
    #                 $iter:=function($t, $p)
    #                   {
    #                     $type($t) = "array"
    #                     ? [$map($t,function($v){$iter($v,$p)})]
    #                     : $type($t) = "object"
    #                       ? (
    #                           $pfx := ($p?($p & ">")) & $t.id & ($t.name?("["&$t.name&"]"));
    #                           $t ~> 
    #                           $sift(function($v, $k){$not($k in ["id","name"])}) ~>
    #                           $each(function($v){$iter($v,$pfx)})
    #                         )
    #                       : $join([$p,$t],">")
    #                   };
    #                 $iter($tree,"")
    #               )                        
    #             };
    #           $pcats := $utils.parse_refs("childIds","children",$sv.bcCategories);                
    #           ($sv.studyDesigns)@$sd.($sd.activities)@$a.
    #             ($a.biomedicalConceptIds)
    #               [
    #                 $count($a.bcCategoryIds) > 0 and
    #                 $ in [$a.bcCategoryIds.$lookup($pcats{id: **.memberIds},$)]
    #               ].
    #               (
    #                 $this := $;
    #                 {
    #                   "instanceType": $a.instanceType,
    #                   "id": $a.id,
    #                   "path": $a._path,
    #                   "StudyDesign.id": $sd.id,
    #                   "StudyDesign.name": $sd.name,
    #                   "name": $a.name,
    #                   "biomedicalConceptId": $this,
    #                   "bcCategoryId(s) containing BC": 
    #                     $utils.sift_tree($pcats[id in $a.bcCategoryIds],$this,["id","name"])~>$flatten
    #                 }
    #               )     
    #         )
    #       ]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00076: not yet implemented")
