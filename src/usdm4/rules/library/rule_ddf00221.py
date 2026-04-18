from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00221(RuleTemplate):
    """
    DDF00221: Within a study design, if more therapeutic areas are defined, they must be distinct.

    Applies to: InterventionalStudyDesign, ObservationalStudyDesign
    Attributes: therapeuticAreas
    """

    def __init__(self):
        super().__init__(
            "DDF00221",
            RuleTemplate.ERROR,
            "Within a study design, if more therapeutic areas are defined, they must be distinct.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study.versions.studyDesigns@$sd.(
    #       $sd.therapeuticAreas.
    #         {
    #           "group": $join([codeSystem,codeSystemVersion,code],"\n"),
    #           "details": $
    #         } {
    #             group:  $count(details)>1
    #                     ? {
    #                         "codeSystem":$distinct(details.codeSystem),
    #                         "codeSystemVersion":$distinct(details.codeSystemVersion),
    #                         "therapeuticAreas":"["&$join($.(details.id&": "&details.decode&" ("&details.code&")"),"; ")&"]"
    #                       }
    #           }
    #       ~>$each(function($v)
    #           {
    #             {
    #               "instanceType": $sd.instanceType,
    #               "id": $sd.id,
    #               "path": $sd._path,
    #               "name": $sd.name,
    #               "therapeuticAreas.codeSystem": $v.codeSystem,
    #               "therapeuticAreas.codeSystemVersion": $v.codeSystemVersion,
    #               "therapeuticAreas": $v.therapeuticAreas
    #             }
    #           }
    #         )
    #       )

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00221: not yet implemented")
