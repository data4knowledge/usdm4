from usdm3.rules.library.rule_template import RuleTemplate

class RuleCHK0250(RuleTemplate):
    """
    CHK0250: Sourcing must not be defined for an administrable product which is only referenced as an embedded product for a medical device. 
    
    Applies to: AdminstrableProduct
    Attributes: sourcing
    """
    
    def __init__(self):
        super().__init__("CHK0250", RuleTemplate.ERROR, "Sourcing must not be defined for an administrable product which is only referenced as an embedded product for a medical device. ")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
