from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class Rule00125(RuleTemplate):
    """
    DDF00125: Attributes must be included as defined in the USDM schema based on the API specification (i.e., all required properties are present and no additional attributes are present).
    
    Applies to: All
    Attributes: All
    """
    
    def __init__(self):
        super().__init__("DDF00125", RuleTemplate.ERROR, "Attributes must be included as defined in the USDM schema based on the API specification (i.e., all required properties are present and no additional attributes are present).")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
