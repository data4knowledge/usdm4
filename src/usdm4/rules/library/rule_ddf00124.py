from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00124(RuleTemplate):
    """
    DDF00124: Referenced items in a parameter map must be available elsewhere in the data model.

    Applies to: ParameterMap
    Attributes: reference
    """

    def __init__(self):
        super().__init__(
            "DDF00124",
            RuleTemplate.ERROR,
            "Referenced items in a parameter map must be available elsewhere in the data model.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (
    #       $lkp:=**[id and instanceType].$each(function($v,$k){{$join([instanceType,id,$k],"|"):$v}})~>$merge;
    #       $.study.**.dictionaries.parameterMaps.
    #           {
    #             "instanceType": instanceType,
    #             "id": id,
    #             "path": _path,
    #             "SyntaxTemplateDictionary.id": %.id,
    #             "SyntaxTemplateDictionary.name": %.name,
    #             "tag": tag,
    #             "reference": reference
    #           }
    #       ~>  $map(function($v)
    #             {
    #               (
    #                 $ref := $match($v.reference,
    #                           /<usdm:ref((?=[^>]* klass=\"([a-zA-Z]+)\")(?=[^>]* id=\"(\w+)\")(?=[^>]* attribute=\"([a-zA-Z]+)\")[^>]*)(\/>|><\/usdm:ref>)/
    #                         )
    #                         {
    #                           "value": $v.reference,
    #                           "usdm_ref": $contains($v.reference,/usdm:ref/) ? 
    #                                       {
    #                                         "klass": groups[1],
    #                                         "id": groups[2],
    #                                         "attribute": groups[3]
    #                                       }
    #                         };
    #                 $v ~> |$|{"reference": $ref}|
    #               )
    #             }
    #           )
    #       ~>  $map(function($v)
    #             {
    #               (
    #                 $ref_val := "usdm_ref" in $keys($v.reference)
    #                             ? (
    #                                 $k := $join(
    #                                         [
    #                                           $v.reference.usdm_ref.klass,
    #                                           $v.reference.usdm_ref.id,
    #                                           $v.reference.usdm_ref.attribute
    #                                         ],"|"
    #                                       );
    #                                 $k in $keys($lkp)
    #                                 ? $lookup($lkp,$k)
    #                                 : "!!NOT FOUND!!"
    #                               )
    #                             : $v.value;
    #                 $v ~> |$|{"reference": $v.reference.value, "Referenced Value": $ref_val}|
    #               )
    #             }
    #           )
    #       ~>  $filter(function($v)
    #             {
    #               $v.`Referenced Value` = "!!NOT FOUND!!"
    #             }
    #           )
    #     )

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00124: not yet implemented")
