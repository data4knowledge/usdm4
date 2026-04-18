from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00256(RuleTemplate):
    """
    DDF00256: The same reason is not expected to be given as a primary and secondary reason.

    Applies to: StudyAmendmentReason
    Attributes: code
    """

    def __init__(self):
        super().__init__(
            "DDF00256",
            RuleTemplate.WARNING,
            "The same reason is not expected to be given as a primary and secondary reason.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.versions.amendments)@$am.
    #       $am.secondaryReasons@$sr.
    #       $sr.
    #           [(
    #               {
    #                   "instanceType": instanceType,
    #                   "id": id,
    #                   "path": _path,
    #                   "StudyAmendment.id": $am.id,
    #                   "StudyAmendment.name": $am.name,
    #                   "code": code.decode & " ("&code.code&")",
    #                   "primaryReason.code": $am.primaryReason.code.decode & " (" & $am.primaryReason.code.code & ")",
    #                   "check": code.code=$am.primaryReason.code.code
    #               }
    #           )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00256: not yet implemented")
