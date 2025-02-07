from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0238(RuleTemplate):
    """
    CHK0238: At least one attribute must be specified for an address.
    
    Applies to: Address
    Attributes: All
    """
    
    def __init__(self):
        super().__init__("CHK0238", RuleTemplate.ERROR, "At least one attribute must be specified for an address.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
