from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00204(RuleTemplate):
    """
    DDF00204: Narrative content must only reference narrative content that is specified within the same study definition document version.

    Applies to: NarrativeContent
    Attributes: next, previous, children
    """

    def __init__(self):
        super().__init__(
            "DDF00204",
            RuleTemplate.ERROR,
            "Narrative content must only reference narrative content that is specified within the same study definition document version.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     $.study.documentedBy@$sdd.
    #       $sdd.versions@$sddv.
    #         $filter(($sddv.contents),function($v)
    #           {
    #             $not(
    #                   $type($v.previousId) = "null" or
    #                   $v.previousId in $sddv.contents.id
    #                 ) or
    #             $not(
    #                   $type($v.nextId) = "null" or
    #                   $v.nextId in $sddv.contents.id
    #                 ) or
    #             $v.childIds[$not($ in $sddv.contents.id)]
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
    #             "Invalid previousId": $not(
    #                                         $type($c.previousId) = "null" or
    #                                         $c.previousId in $sddv.contents.id
    #                                       )
    #                                   ? $c.previousId,
    #             "Invalid nextId": $not(
    #                                     $type($c.nextId) = "null" or
    #                                     $c.nextId in $sddv.contents.id
    #                                   )
    #                               ? $c.nextId,
    #             "Invalid childIds": $c.childIds[$not($ in $sddv.contents.id)] ~> $join("; ")
    #           }

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00204: not yet implemented")
