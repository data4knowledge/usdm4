from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00245(RuleTemplate):
    """
    DDF00245: Within a document version, the specified section numbers for narrative content must be unique.

    Applies to: NarrativeContent
    Attributes: sectionNumber
    """

    def __init__(self):
        super().__init__(
            "DDF00245",
            RuleTemplate.ERROR,
            "Within a document version, the specified section numbers for narrative content must be unique.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     $.study.documentedBy@$sdd.
    #       $sdd.versions@$sddv.
    #         (
    #           $sddv.contents[displaySectionNumber=true and sectionNumber].
    #             {
    #               "group": $join([$sdd.id,$sddv.id,sectionNumber],"\n"),
    #               "details":
    #                 {
    #                   "instanceType": instanceType,
    #                   "id": id,
    #                   "path": _path,
    #                   "StudyDefinitionDocument.id": $sdd.id,
    #                   "StudyDefinitionDocument.name": $sdd.name,
    #                   "StudyDefinitionDocumentVersion.id": $sddv.id,
    #                   "StudyDefinitionDocumentVersion.version": $sddv.version,
    #                   "name": name,
    #                   "sectionNumber": sectionNumber,
    #                   "displaySectionNumber": displaySectionNumber
    #                 }
    #             } {group: $count(details)>1?details}
    #           ).*

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00245: not yet implemented")
