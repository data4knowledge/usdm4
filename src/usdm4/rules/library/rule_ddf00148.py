from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class Rule00148(RuleTemplate):
    """
    DDF00148: An endpoint level must be specified using the endpoint level (C188726) DDF codelist.
    
    Applies to: Endpoint
    Attributes: level
    """
    
    def __init__(self):
        super().__init__("DDF00148", RuleTemplate.ERROR, "An endpoint level must be specified using the endpoint level (C188726) DDF codelist.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
