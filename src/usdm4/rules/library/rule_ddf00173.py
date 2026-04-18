from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00173(RuleTemplate):
    """
    DDF00173: Every identifier must be unique within the scope of an identified organization.

    Applies to: StudyIdentifier, ReferenceIdentifier, AdministrableProductIdentifier, MedicalDeviceIdentifier
    Attributes: text
    """

    def __init__(self):
        super().__init__(
            "DDF00173",
            RuleTemplate.ERROR,
            "Every identifier must be unique within the scope of an identified organization.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study.versions@$sv.
    #       (
    #         $sv.**.*[scopeId and text and instanceType]
    #           {
    #             $join([text,scopeId,instanceType],"\n"):
    #               (
    #                 $i:=$;
    #                 $count($i) > 1 ? $i.
    #                   {
    #                     "instanceType": instanceType,
    #                     "id": id,
    #                     "path": _path,
    #                     "text": text,
    #                     "scopeId": scopeId,
    #                     "Organization.name": ($si:=scopeId;$sv.organizations[id=$si].name),
    #                     "type.decode": type.decode
    #                   }
    #               )
    #           }
    #       ).*

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00173: not yet implemented")
