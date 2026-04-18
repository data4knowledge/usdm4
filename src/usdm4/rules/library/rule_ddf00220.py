from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00220(RuleTemplate):
    """
    DDF00220: Within a study design, if more sub types are defined, they must be distinct.

    Applies to: InterventionalStudyDesign, ObservationalStudyDesign
    Attributes: subTypes
    """

    def __init__(self):
        super().__init__(
            "DDF00220",
            RuleTemplate.ERROR,
            "Within a study design, if more sub types are defined, they must be distinct.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study.versions.studyDesigns.
    #       (
    #         subTypes
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
    #               "subTypes": $v
    #             }
    #           }
    #         )
    #       )  

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00220: not yet implemented")
