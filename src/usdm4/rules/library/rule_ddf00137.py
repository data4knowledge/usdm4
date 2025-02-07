from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class Rule00137(RuleTemplate):
    """
    DDF00137: References must be a fixed value or a reference to items stored elsewhere in the data model which must be specified in the correct format. They must start with '<usdm:ref', end with either '/>' or '></usdm:ref>', and must contain 'klass=\"klassName\"', 'id=\"idValue\"', and 'attribute=\"attributeName\"/>' in any order (where \"klassName\" and \"attributeName\" contain only letters in upper or lower case).
    
    Applies to: ParameterMap
    Attributes: reference
    """
    
    def __init__(self):
        super().__init__("DDF00137", RuleTemplate.ERROR, "References must be a fixed value or a reference to items stored elsewhere in the data model which must be specified in the correct format. They must start with '<usdm:ref', end with either '/>' or '></usdm:ref>', and must contain 'klass=\"klassName\"', 'id=\"idValue\"', and 'attribute=\"attributeName\"/>' in any order (where \"klassName\" and \"attributeName\" contain only letters in upper or lower case).")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
