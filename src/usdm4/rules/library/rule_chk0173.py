from usdm3.rules.library.rule_template import RuleTemplate

class RuleCHK0173(RuleTemplate):
    """
    CHK0173: Each defined elibility criterion must be used by at least one study population or cohort.
    
    Applies to: StudyVersion
    Attributes: criteria
    """
    
    def __init__(self):
        super().__init__("CHK0173", RuleTemplate.ERROR, "Each defined elibility criterion must be used by at least one study population or cohort.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
