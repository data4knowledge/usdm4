from usdm3.rules.library.rule_template import RuleTemplate

class RuleCHK0192(RuleTemplate):
    """
    CHK0192: The long names for all abbreviations defined for a study version are expected to be unique.
    
    Applies to: Abbreviation
    Attributes: longName
    """
    
    def __init__(self):
        super().__init__("CHK0192", RuleTemplate.ERROR, "The long names for all abbreviations defined for a study version are expected to be unique.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
