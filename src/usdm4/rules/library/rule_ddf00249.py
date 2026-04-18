from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00249(RuleTemplate):
    """
    DDF00249: An eligibility criterion item is expected to be used in at least one study design.

    Applies to: EligibilityCriterion
    Attributes: criterionItem
    """

    def __init__(self):
        super().__init__(
            "DDF00249",
            RuleTemplate.WARNING,
            "An eligibility criterion item is expected to be used in at least one study design.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study.versions@$sv.
    #       $sv.eligibilityCriterionItems
    #         [
    #           $not(id in $sv.studyDesigns.eligibilityCriteria.criterionItemId)
    #         ].
    #         {
    #           "instanceType": instanceType,
    #           "id": id,
    #           "path": _path,
    #           "StudyVersion.id": $sv.id,
    #           "StudyVersion.versionIdentifier": $sv.versionIdentifier,
    #           "name": name
    #         }

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00249: not yet implemented")
