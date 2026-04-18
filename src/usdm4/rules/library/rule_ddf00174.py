from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00174(RuleTemplate):
    """
    DDF00174: An identified organization is not expected to have more than 1 identifier for the study.

    Applies to: StudyIdentifier
    Attributes: scope
    """

    def __init__(self):
        super().__init__(
            "DDF00174",
            RuleTemplate.WARNING,
            "An identified organization is not expected to have more than 1 identifier for the study.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study.versions@$sv.
    #       (
    #         $sv.organizations
    #           {
    #             id: 
    #               (
    #                 $o:=$;
    #                 $i:=$sv.studyIdentifiers[scopeId=$o.id];
    #                 $count($i) > 1 ? $i.
    #                   {
    #                     "instanceType": instanceType,
    #                     "id": id,
    #                     "path": _path,
    #                     "text": text,
    #                     "scopeId": scopeId,
    #                     "Organization.name": $o.name
    #                   }
    #               )
    #           }
    #       ).*

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00174: not yet implemented")
