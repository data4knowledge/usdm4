from usdm3.rules.library.rule_template import RuleTemplate

class RuleCHK0201(RuleTemplate):
    """
    CHK0201: If an administration's dose is specified then a corresponding route is expected and vice versa.
    
    Applies to: Administration
    Attributes: dose, route
    """
    
    def __init__(self):
        super().__init__("CHK0201", RuleTemplate.ERROR, "If an administration's dose is specified then a corresponding route is expected and vice versa.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
