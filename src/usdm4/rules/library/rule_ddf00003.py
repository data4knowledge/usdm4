from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class Rule00003(RuleTemplate):
    """
    DDF00003: If the duration of an administration will vary, a quantity is not expected for the administration duration and vice versa.
    
    Applies to: AdministrationDuration
    Attributes: quantity
    """
    
    def __init__(self):
        super().__init__("DDF00003", RuleTemplate.ERROR, "If the duration of an administration will vary, a quantity is not expected for the administration duration and vice versa.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
