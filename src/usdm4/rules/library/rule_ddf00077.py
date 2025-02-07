from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class Rule00077(RuleTemplate):
    """
    DDF00077: If geographic scope type is global then no codes are expected to specify the specific area within scope while if it is not global then at least one code is expected to specify the specific area within scope.
    
    Applies to: GeographicScope
    Attributes: code
    """
    
    def __init__(self):
        super().__init__("DDF00077", RuleTemplate.ERROR, "If geographic scope type is global then no codes are expected to specify the specific area within scope while if it is not global then at least one code is expected to specify the specific area within scope.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
