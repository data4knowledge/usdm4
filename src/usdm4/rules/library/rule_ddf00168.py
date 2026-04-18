from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00168(RuleTemplate):
    """
    DDF00168: A piece of narrative content must only reference narrative content items that have been defined within the study version as the narrative content.

    Applies to: NarrativeContent
    Attributes: contentItem
    """

    def __init__(self):
        super().__init__(
            "DDF00168",
            RuleTemplate.ERROR,
            "A piece of narrative content must only reference narrative content items that have been defined within the study version as the narrative content.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.**.study)@$s.$s.documentedBy@$sd.
    #       $sd.versions@$sv.
    #       $sv.contents@$nc.
    #       $nc.
    #         [
    #           ($ChkX:=function()
    #             {
    #               contentItemId and $not(contentItemId in $s.versions.narrativeContentItems.id)
    #             };
    #             {
    #               "instanceType": $nc.instanceType,
    #               "id": $nc.id,
    #               "path": $nc._path,
    #               "StudyDefinitionDocument.id": $sd.id,
    #               "StudyDefinitionDocument.name": $sd.name,
    #               "StudyDefinitionDocumentVersion.id": $sv.id,
    #               "StudyDefinitionDocumentVersion.version": $sv.version,
    #               "name": $nc.name,
    #               "contentItemId": $nc.contentItemId,
    #               "sectionNumber": $nc.sectionNumber,
    #               "check": $ChkX()
    #             }
    #           )
    #         ]
    #         [check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00168: not yet implemented")
