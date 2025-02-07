from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0191(RuleTemplate):
    """
    CHK0191: All abbreviations defined for a study version must be unique.
    
    Applies to: Abbreviation
    Attributes: abbreviation
    """
    
    def __init__(self):
        super().__init__("CHK0191", RuleTemplate.ERROR, "All abbreviations defined for a study version must be unique.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
