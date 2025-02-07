from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class Rule00010(RuleTemplate):
    """
    DDF00010: The names of all child instances of the same parent class must be unique.
    
    Applies to: All
    Attributes: name
    """
    
    def __init__(self):
        super().__init__("DDF00010", RuleTemplate.ERROR, "The names of all child instances of the same parent class must be unique.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
