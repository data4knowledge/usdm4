from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00163(RuleTemplate):
    """
    DDF00163: Narrative content is expected to point to a child and/or to a content item text.

    Applies to: NarrativeContent
    Attributes: children, contentItem
    """

    def __init__(self):
        super().__init__(
            "DDF00163",
            RuleTemplate.WARNING,
            "Narrative content is expected to point to a child and/or to a content item text.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     $.study.documentedBy@$sdd.
    #       $sdd.versions@$sddv.
    #         $filter(($sddv.contents),function($v)
    #           {
    #             $not($v.childIds or $v.contentItemId)
    #           }
    #         )@$c.
    #           {
    #             "instanceType": $c.instanceType,
    #             "id": $c.id,
    #             "path": $c._path,
    #             "StudyDefinitionDocument.id": $sdd.id,
    #             "StudyDefinitionDocument.name": $sdd.name,
    #             "StudyDefinitionDocumentVersion.id": $sddv.id,
    #             "StudyDefinitionDocumentVersion.version": $sddv.version,
    #             "name": $c.name,
    #             "sectionNumber": $c.sectionNumber,
    #             "sectionTitle": $c.sectionTitle
    #           }

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00163: not yet implemented")
