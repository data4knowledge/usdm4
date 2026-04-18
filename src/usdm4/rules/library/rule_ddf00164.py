from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00164(RuleTemplate):
    """
    DDF00164: If a section number is to be displayed then a number must be specified and vice versa.

    Applies to: NarrativeContent
    Attributes: sectionNumber, displaySectionNumber
    """

    def __init__(self):
        super().__init__(
            "DDF00164",
            RuleTemplate.ERROR,
            "If a section number is to be displayed then a number must be specified and vice versa.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.**.documentedBy)@$db.
    #       $db.versions@$sv.
    #       $sv.contents@$nc.
    #       $nc.
    #         [
    #           (
    #             $NoSectNo:=function(){$type($nc.sectionNumber)="null" or sectionNumber="" or $exists(sectionNumber)=false} ;
    #             $ChkX:=function()
    #               {
    #                 ($NoSectNo()=true and displaySectionNumber=true)
    #               };
    #               {
    #                 "instanceType": $nc.instanceType,
    #                 "id": $nc.id,
    #                 "path": $nc._path,
    #                 "StudyDefinitionDocument.id": $db.id,
    #                 "StudyDefinitionDocument.name": $db.name,
    #                 "StudyDefinitionDocumentVersion.id": $sv.id,
    #                 "StudyDefinitionDocumentVersion.version": $sv.version,
    #                 "name": $nc.name,
    #                 "displaySectionNumber": $nc.displaySectionNumber,
    #                 "sectionNumber": $nc.sectionNumber,
    #                 "check": $ChkX()
    #               }
    #           )
    #         ]
    #         [check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00164: not yet implemented")
