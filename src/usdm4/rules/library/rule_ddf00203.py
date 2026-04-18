from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00203(RuleTemplate):
    """
    DDF00203: The sponsor study role must be applicable to a study version.

    Applies to: StudyRole
    Attributes: appliesTo
    """

    def __init__(self):
        super().__init__(
            "DDF00203",
            RuleTemplate.ERROR,
            "The sponsor study role must be applicable to a study version.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study.versions@$sv.
    #       ($sv.roles[code.code = "C70793" and $not($sv.id in appliesToIds)])@$r.
    #         {
    #           "instanceType": $r.instanceType,
    #           "id": $r.id,
    #           "path": $r._path,
    #           "name": $r.name,
    #           "code.code": $r.code.code,
    #           "code.decode": $r.code.decode,
    #           "appliesToIds": $r.appliesToIds[],
    #           "StudyVersion.id": $sv.id
    #         }

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00203: not yet implemented")
