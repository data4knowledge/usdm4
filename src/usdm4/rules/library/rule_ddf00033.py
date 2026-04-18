from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00033(RuleTemplate):
    """
    DDF00033: At least the text or the quantity must be specified for a duration.

    Applies to: Duration
    Attributes: text, quantity
    """

    def __init__(self):
        super().__init__(
            "DDF00033",
            RuleTemplate.ERROR,
            "At least the text or the quantity must be specified for a duration.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.**[instanceType="Duration"])@$d.
    #       $d.[{
    #                               "instanceType": $d.instanceType,
    #                               "id": $d.id,
    #                               "path": $d._path,
    #                               "text": $d.text,
    #                               "quantity": quantity,
    #                               "check": $not(text or quantity)
    #                               }][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00033: not yet implemented")
