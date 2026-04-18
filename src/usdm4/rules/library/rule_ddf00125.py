from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00125(RuleTemplate):
    """
    DDF00125: Attributes must be included as defined in the USDM schema based on the API specification (i.e., all required properties are present and no additional attributes are present).

    Applies to: All
    Attributes: All
    """

    def __init__(self):
        super().__init__(
            "DDF00125",
            RuleTemplate.ERROR,
            "Attributes must be included as defined in the USDM schema based on the API specification (i.e., all required properties are present and no additional attributes are present).",
        )

    # TODO: implement. HIGH_CT_MEMBER with class='All' attr='validator' — likely a schema-conformance rule, not CT lookup. Needs hand-authoring.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00125: not yet implemented")
