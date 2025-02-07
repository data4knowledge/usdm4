from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0252(RuleTemplate):
    """
    CHK0252: An administrable product sourcing must be specified using the sourcing (Cxxx) DDF codelist.
    
    Applies to: AdministrableProduct
    Attributes: sourcing
    """
    
    def __init__(self):
        super().__init__("CHK0252", RuleTemplate.ERROR, "An administrable product sourcing must be specified using the sourcing (Cxxx) DDF codelist.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
