from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class Rule00084(RuleTemplate):
    """
    DDF00084: Within a study design there must be exactly one objective with level 'Primary Objective'.
    
    Applies to: Objective
    Attributes: level
    """
    
    def __init__(self):
        super().__init__("DDF00084", RuleTemplate.ERROR, "Within a study design there must be exactly one objective with level 'Primary Objective'.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
