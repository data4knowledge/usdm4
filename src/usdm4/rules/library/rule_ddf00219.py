from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00219(RuleTemplate):
    """
    DDF00219: Within a study design, if more characteristics are defined, they must be distinct.

    Applies to: InterventionalStudyDesign, ObservationalStudyDesign
    Attributes: characteristics
    """

    def __init__(self):
        super().__init__(
            "DDF00219",
            RuleTemplate.ERROR,
            "Within a study design, if more characteristics are defined, they must be distinct.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study.versions.studyDesigns.
    #       (
    #         characteristics
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
    #               "characteristics": $v
    #             }
    #           }
    #         )
    #       )  

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00219: not yet implemented")
