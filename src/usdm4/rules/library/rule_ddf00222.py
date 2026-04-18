from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00222(RuleTemplate):
    """
    DDF00222: Within a study design, if more intent types are defined, they must be distinct.

    Applies to: InterventionalStudyDesign
    Attributes: intentTypes
    """

    def __init__(self):
        super().__init__(
            "DDF00222",
            RuleTemplate.ERROR,
            "Within a study design, if more intent types are defined, they must be distinct.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study.versions.studyDesigns.
    #       (
    #         intentTypes
    #           {
    #               code: $count(id)>1?"["&$join($.(id&": "&decode&" ("&code&")"),"; ")&"]"
    #           } ~>
    #         $each(
    #           function($v){
    #             {
    #               "instanceType": instanceType,
    #               "id": id,
    #               "path": _path,
    #               "name": name,
    #               "intentTypes": $v
    #             }
    #           }
    #         )
    #       )  

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00222: not yet implemented")
