from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00158(RuleTemplate):
    """
    DDF00158: Each defined eligibility criterion must be used by at least one study population or cohort within the same study design.

    Applies to: ObservationalStudyDesign, InterventionalStudyDesign
    Attributes: criteria
    """

    def __init__(self):
        super().__init__(
            "DDF00158",
            RuleTemplate.ERROR,
            "Each defined eligibility criterion must be used by at least one study population or cohort within the same study design.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.**.studyDesigns)@$s.
    #       $s.eligibilityCriteria@$ec
    #         [
    #           $not($ec.id in $append($s.population.criterionIds,$s.population.cohorts.criterionIds))
    #         ].
    #         {
    #           "instanceType": $ec.instanceType,
    #           "id": $ec.id,
    #           "path": $ec._path,
    #           "StudyDesign.id": $s.id,
    #           "StudyDesign.name": $s.name,
    #           "name": $ec.name,
    #           "category": $ec.category.decode,
    #           "identifier": $ec.identifier
    #         }

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00158: not yet implemented")
