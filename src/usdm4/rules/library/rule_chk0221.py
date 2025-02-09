from usdm3.rules.library.rule_template import RuleTemplate

class RuleCHK0221(RuleTemplate):
    """
    CHK0221: A unit must be specified for every strength denominator and numerator
    
    Applies to: Strength
    Attributes: numerator, denominator
    """
    
    def __init__(self):
        super().__init__("CHK0221", RuleTemplate.ERROR, "A unit must be specified for every strength denominator and numerator")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
