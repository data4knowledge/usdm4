from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00030(RuleTemplate):
    """
    DDF00030: At least the text or the family name must be specified for a person name.

    Applies to: PersonName
    Attributes: text, familyName
    """

    def __init__(self):
        super().__init__(
            "DDF00030",
            RuleTemplate.ERROR,
            "At least the text or the family name must be specified for a person name.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.**[instanceType="PersonName"])@$pn.
    #       $pn.
    #           [(  {
    #                   "instanceType": instanceType,
    #                   "id": id,
    #                   "path": _path,
    #                   "familyName": familyName,
    #                   "text": text,
    #                   "check":  $not(familyName or text)
    #               }
    #           )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00030: not yet implemented")
