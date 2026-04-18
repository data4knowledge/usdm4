from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00227(RuleTemplate):
    """
    DDF00227: An interventional study must be specified using the InterventionalStudyDesign class.

    Applies to: InterventionalStudyDesign
    Attributes: studyType
    """

    def __init__(self):
        super().__init__(
            "DDF00227",
            RuleTemplate.ERROR,
            "An interventional study must be specified using the InterventionalStudyDesign class.",
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
    #                       "check": studyType.code="C98388" and instanceType != "InterventionalStudyDesign"
    #                   }
    #           )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00227: not yet implemented")
