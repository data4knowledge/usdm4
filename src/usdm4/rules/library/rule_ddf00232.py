from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00232(RuleTemplate):
    """
    DDF00232: An observational study (including patient registries) is expected to have a study phase decode value of "NOT APPLICABLE".

    Applies to: ObservationalStudyDesign
    Attributes: studyPhase
    """

    def __init__(self):
        super().__init__(
            "DDF00232",
            RuleTemplate.WARNING,
            'An observational study (including patient registries) is expected to have a study phase decode value of "NOT APPLICABLE".',
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.versions)@$sv.
    #              $sv.studyDesigns@$sd.
    #              $sd.    
    #              [({
    #                     "instanceType": instanceType,
    #                     "id": id,
    #                     "path": _path,
    #                     "name": name,
    #                     "studyType": studyType ? studyType.decode & " (" & studyType.code & ")",
    #                     "studyPhase": studyPhase ? studyPhase.standardCode.decode & " (" & studyPhase.standardCode.code & ")",
    #                     "check": studyType.code in ["C16084","C129000"] and studyPhase.standardCode.code !="C48660"
    #                 }
    #               )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00232: not yet implemented")
