from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00243(RuleTemplate):
    """
    DDF00243: Each StudyArm is expected to have one StudyCell for each StudyEpoch.

    Applies to: StudyCell
    Attributes: arm, epoch
    """

    def __init__(self):
        super().__init__(
            "DDF00243",
            RuleTemplate.WARNING,
            "Each StudyArm is expected to have one StudyCell for each StudyEpoch.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study.versions.studyDesigns@$sd.
    #       $sd.arms@$sa.{
    #       $sa.id:
    #           {
    #           "instanceType": $sa.instanceType,
    #           "id": $sa.id,
    #           "path": $sa._path,
    #           "StudyDesign.id": $sd.id,
    #           "StudyDesign.name": $sd.name,
    #           "name": $sa.name,
    #           "StudyDesign.epochs": "["&$join($sd.epochs.(id&": "&name),"; ")&"]",
    #           "Arm's StudyCell Epoch Refs": "["&$join($sd.studyCells[armId=$sa.id].($sc:=$;id&": "&epochId&" ("&($sc.epochId in $sd.epochs.id?$sd.epochs[id=$sc.epochId].name:"Invalid epochId")&")"),"; ")&"]",
    #           "Missing Epoch Refs": "["&$join($sd.epochs[$not(id in $sd.studyCells[armId=$sa.id].epochId)].(id&": "&name),"; ")&"]"
    #           }
    #       }.*[`Missing Epoch Refs`!="[]"]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00243: not yet implemented")
