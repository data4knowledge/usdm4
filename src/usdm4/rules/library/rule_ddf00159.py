from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00159(RuleTemplate):
    """
    DDF00159: An eligibility criterion must not be referenced by both a study design population and any of the cohorts of the same study design population.

    Applies to: ObservationalStudyDesign, InterventionalStudyDesign
    Attributes: criteria
    """

    def __init__(self):
        super().__init__(
            "DDF00159",
            RuleTemplate.ERROR,
            "An eligibility criterion must not be referenced by both a study design population and any of the cohorts of the same study design population.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.**.studyDesigns)@$s.
    #       $s.eligibilityCriteria@$ec
    #         [
    #           $ec.id in $s.population.criterionIds and
    #           $ec.id in $s.population.cohorts.criterionIds
    #         ].
    #         {
    #           "instanceType": $ec.instanceType,
    #           "id": $ec.id,
    #           "path": $ec._path,
    #           "StudyDesign.id": $s.id,
    #           "StudyDesign.name": $s.name,
    #           "name": $ec.name,
    #           "category": $ec.category.decode,
    #           "identifier": $ec.identifier,
    #           "Used in": $s.**[$ec.id in $.criterionIds].(id&(name?"["&name&"]"))
    #         }

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00159: not yet implemented")
