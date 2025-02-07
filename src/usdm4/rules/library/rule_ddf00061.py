from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class Rule00061(RuleTemplate):
    """
    DDF00061: When specified, the lower limit of a timing window must be a non-negative duration in ISO 8601 format.
    
    Applies to: Timing
    Attributes: windowLower
    """
    
    def __init__(self):
        super().__init__("DDF00061", RuleTemplate.ERROR, "When specified, the lower limit of a timing window must be a non-negative duration in ISO 8601 format.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
