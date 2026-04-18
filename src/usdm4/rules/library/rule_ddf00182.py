from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00182(RuleTemplate):
    """
    DDF00182: Within a study protocol document version, if a date of a specific type exists with a global geographic scope then no other dates are expected with the same type.

    Applies to: StudyDefinitionDocumentVersion
    Attributes: dateValues
    """

    def __init__(self):
        super().__init__(
            "DDF00182",
            RuleTemplate.WARNING,
            "Within a study protocol document version, if a date of a specific type exists with a global geographic scope then no other dates are expected with the same type.",
        )

    # TODO: implement. MED_TEXT predicate='conditional': no template — typically a rule-specific conditional. Hand-author using the JSONata reference below.
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study@$s.
    #       $s.documentedBy@$sdd.
    #         $sdd.versions@$sddv.
    #           ($sddv.dateValues["C68846" in geographicScopes.type.code])@$gdv.
    #             (
    #               $sddv.dateValues[type.code in $gdv.type.code]
    #                 {
    #                   type.code:$count($)>1
    #                             ? $.{
    #                                   "instanceType": instanceType,
    #                                   "id": id,
    #                                   "path": _path,
    #                                   "StudyDefinitionDocument.id": $sdd.id,
    #                                   "StudyDefinitionDocument.name": $sdd.name,
    #                                   "StudyDefinitionDocumentVersion.id": $sddv.id,
    #                                   "StudyDefinitionDocumentVersion.version": $sddv.version,
    #                                   "type": type.decode&" ("&type.code&")",
    #                                   "dateValue": dateValue,
    #                                   "geographicScopes.type": "["&$join(geographicScopes.(id & ": " & type.decode & " (" & type.code & ")"),"; ")&"]"
    #                                 }
    #                 }
    #               ).* ~> $distinct

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00182: not yet implemented")
