from usdm3.rules.library.rule_template import RuleTemplate

class RuleCHK0219(RuleTemplate):
    """
    CHK0219: A referenced substance must not have any references itself.
    
    Applies to: Substance
    Attributes: referenceSubstance
    """
    
    def __init__(self):
        super().__init__("CHK0219", RuleTemplate.ERROR, "A referenced substance must not have any references itself.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
