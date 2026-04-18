from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00228(RuleTemplate):
    """
    DDF00228: An observational study (including patient registries) must be specified using the ObservationalStudyDesign class.

    Applies to: ObservationalStudyDesign
    Attributes: studyType
    """

    def __init__(self):
        super().__init__(
            "DDF00228",
            RuleTemplate.ERROR,
            "An observational study (including patient registries) must be specified using the ObservationalStudyDesign class.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.versions)@$sv.
    #       $sv.studyDesigns@$sd.
    #       $sd.    [({
    #                       "instanceType": instanceType,
    #                       "id": id,
    #                       "path": _path,
    #                       "name": name,
    #                       "studyType": studyType ? studyType.decode & " (" & studyType.code & ")",
    #                       "check": studyType.code in ["C16084","C129000"] and instanceType != "ObservationalStudyDesign"
    #                   }
    #           )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00228: not yet implemented")
