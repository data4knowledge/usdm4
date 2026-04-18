from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00050(RuleTemplate):
    """
    DDF00050: A study arm must only reference study populations or cohorts that are defined within the same study design as the study arm.

    Applies to: StudyArm
    Attributes: populations
    """

    def __init__(self):
        super().__init__(
            "DDF00050",
            RuleTemplate.ERROR,
            "A study arm must only reference study populations or cohorts that are defined within the same study design as the study arm.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.**.studyDesigns)@$s.
    #       [
    #         $s.arms.populationIds[$ != $s.population.id and $not($ in $s.population.cohorts.id)].
    #           {
    #             "instanceType": %.instanceType,
    #             "id": %.id,
    #             "path": %._path,
    #             "StudyDesign.id": $s.id,
    #             "StudyDesign.name": $s.name,
    #             "StudyDesign.population.id": $s.population.id,
    #             "StudyDesign.population.cohorts.id": $s.population.cohorts.id,
    #             "name": %.name,
    #             "populationId": $
    #           }
    #       ]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00050: not yet implemented")
