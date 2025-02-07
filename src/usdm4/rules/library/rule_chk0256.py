from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0256(RuleTemplate):
    """
    CHK0256: If 'appliesTo' is specified for a product organization role, then the product organization role must only apply to medical devices or administrable products.
    
    Applies to: ProductOrganizationRole
    Attributes: appliesTo
    """
    
    def __init__(self):
        super().__init__("CHK0256", RuleTemplate.ERROR, "If 'appliesTo' is specified for a product organization role, then the product organization role must only apply to medical devices or administrable products.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
