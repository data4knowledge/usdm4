from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00260(RuleTemplate):
    """
    DDF00260: Id values are expected not to have spaces in their string values.

    Applies to: All
    Attributes: id
    """

    def __init__(self):
        super().__init__(
            "DDF00260",
            RuleTemplate.WARNING,
            "Id values are expected not to have spaces in their string values.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (**[$contains($string(id)," ")])@$i.
    #       {
    #         "instanceType": $i.instanceType,
    #         "id": $join(['"','"'],$i.id),
    #         "path": $i._path,
    #         "name": $i.name
    #       }

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00260: not yet implemented")
