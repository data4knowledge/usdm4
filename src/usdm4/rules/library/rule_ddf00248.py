from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00248(RuleTemplate):
    """
    DDF00248: An eligibility criterion item must not be used more than once within a study design.

    Applies to: EligibilityCriterion
    Attributes: criterionItem
    """

    def __init__(self):
        super().__init__(
            "DDF00248",
            RuleTemplate.ERROR,
            "An eligibility criterion item must not be used more than once within a study design.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study.versions.studyDesigns@$sd.
    #       (
    #         $sd.eligibilityCriteria.
    #           {
    #             "group": $join([$sd.id,criterionItemId],"\n"),
    #             "details": 
    #             { 
    #                 "instanceType": instanceType,
    #                 "id": id,
    #                 "path": _path,
    #                 "StudyDesign.id": $sd.id,
    #                 "StudyDesign.name": $sd.name,
    #                 "name": name,
    #                 "criterionItemId": criterionItemId
    #             }
    #           }{group:$count(details)>1?details}
    #       ).*

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00248: not yet implemented")
