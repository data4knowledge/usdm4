from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00162(RuleTemplate):
    """
    DDF00162: When included in text, references to items stored elsewhere in the data model must be specified in the correct format. They must start with '<usdm:ref', end with either '/>' or '></usdm:ref>', and must contain 'klass="KlassName"',  'id="idValue"', and 'attribute="attributeName"/>' in any order (where "KlassName" and "attributeName" contain only letters in upper or lower case).

    Applies to: NarrativeContentItem
    Attributes: text
    """

    def __init__(self):
        super().__init__(
            "DDF00162",
            RuleTemplate.ERROR,
            "When included in text, references to items stored elsewhere in the data model must be specified in the correct format. They must start with '<usdm:ref', end with either '/>' or '></usdm:ref>', and must contain 'klass=\"KlassName\"',  'id=\"idValue\"', and 'attribute=\"attributeName\"/>' in any order (where \"KlassName\" and \"attributeName\" contain only letters in upper or lower case).",
        )

    # TODO: implement. STUB: rule not present in CORE catalogue
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00162: not yet implemented")
