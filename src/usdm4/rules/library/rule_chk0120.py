from usdm3.rules.library.rule_template import RuleTemplate

class RuleCHK0120(RuleTemplate):
    """
    CHK0120: For a specified range at least a minimum or maximum value is expected.
    
    Applies to: Range
    Attributes: minValue, maxValue
    """
    
    def __init__(self):
        super().__init__("CHK0120", RuleTemplate.ERROR, "For a specified range at least a minimum or maximum value is expected.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
