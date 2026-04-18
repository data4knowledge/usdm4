from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00251(RuleTemplate):
    """
    DDF00251: A study cohort must only reference indications that are  defined within the same study design.

    Applies to: StudyCohort
    Attributes: indications
    """

    def __init__(self):
        super().__init__(
            "DDF00251",
            RuleTemplate.ERROR,
            "A study cohort must only reference indications that are  defined within the same study design.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.**.studyDesigns)@$sd.
    #          $sd.population@$sp.
    #          $sp.cohorts[$count(indicationIds[$not($ in $sd.indications.id)])>0].
    #              {
    #              "instanceType": instanceType,
    #              "id": id,
    #              "path": _path,
    #              "StudyDesign.id": $sd.id,
    #              "StudyDesign.name": $sd.name,
    #              "StudyDesign.indications.id": $sd.indications.id,
    #              "StudyDesignPopulation.id": $sp.id,
    #              "StudyDesignPopulation.name": $sp.name,
    #              "name": name,
    #              "Invalid indicationIds": indicationIds[$not($ in $sd.indications.id)]
    #              }

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00251: not yet implemented")
