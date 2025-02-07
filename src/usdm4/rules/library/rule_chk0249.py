from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0249(RuleTemplate):
    """
    CHK0249: An administrable product must not be referenced as both the administrable product for an administration and the embedded product of a medical device that is referenced by the same administration.
    
    Applies to: Administration
    Attributes: administrableProduct
    """
    
    def __init__(self):
        super().__init__("CHK0249", RuleTemplate.ERROR, "An administrable product must not be referenced as both the administrable product for an administration and the embedded product of a medical device that is referenced by the same administration.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
