from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00165(RuleTemplate):
    """
    DDF00165: If a section title is to be displayed then a title must be specified and vice versa.

    Applies to: NarrativeContent
    Attributes: sectionTitle, displaySectionTitle
    """

    def __init__(self):
        super().__init__(
            "DDF00165",
            RuleTemplate.ERROR,
            "If a section title is to be displayed then a title must be specified and vice versa.",
        )

    # TODO: implement. MED_TEXT predicate='conditional': no template — typically a rule-specific conditional. Hand-author using the JSONata reference below.
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.**.documentedBy)@$db.
    #       $db.versions@$sv.
    #       $sv.contents@$nc.
    #       $nc.
    #         [
    #           (
    #             $NoSect:=function(){$type($nc.sectionTitle)="null" or sectionTitle="" or $exists(sectionTitle)=false} ;
    #             $ChkX:=function()
    #               {
    #                 ($NoSect()=true and displaySectionTitle=true)
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
    #                 "displaySectionTitle": $nc.displaySectionTitle,
    #                 "sectionTitle": $nc.sectionTitle,
    #                 "check": $ChkX()
    #               }
    #           )
    #         ]
    #         [check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00165: not yet implemented")
