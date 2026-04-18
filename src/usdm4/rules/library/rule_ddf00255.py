from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00255(RuleTemplate):
    """
    DDF00255: A primary study amendment reason is not expected to be 'not applicable'.

    Applies to: StudyAmendmentReason
    Attributes: code
    """

    def __init__(self):
        super().__init__(
            "DDF00255",
            RuleTemplate.WARNING,
            "A primary study amendment reason is not expected to be 'not applicable'.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.versions.amendments)@$am.
    #       $am.primaryReason@$pr.
    #       $pr.
    #           [(
    #               {
    #                   "instanceType": instanceType,
    #                   "id": id,
    #                   "path": _path,
    #                   "StudyAmendment.id": $am.id,
    #                   "StudyAmendment.name": $am.name,
    #                   "code": code.decode & " ("&code.code&")",
    #                   "check": code.code="C48660"
    #               }
    #           )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00255: not yet implemented")
