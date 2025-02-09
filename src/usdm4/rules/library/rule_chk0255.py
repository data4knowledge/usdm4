from usdm3.rules.library.rule_template import RuleTemplate

class RuleCHK0255(RuleTemplate):
    """
    CHK0255: A product organization role is expected to apply to at least one medical device or administrable product.
    
    Applies to: ProductOrganizationRole
    Attributes: appliesTo
    """
    
    def __init__(self):
        super().__init__("CHK0255", RuleTemplate.ERROR, "A product organization role is expected to apply to at least one medical device or administrable product.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
