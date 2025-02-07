from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0202(RuleTemplate):
    """
    CHK0202: If a dose is specified then a corresponding frequency must also be specified.
    
    Applies to: Administration
    Attributes: dose
    """
    
    def __init__(self):
        super().__init__("CHK0202", RuleTemplate.ERROR, "If a dose is specified then a corresponding frequency must also be specified.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
