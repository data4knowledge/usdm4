from usdm3.rules.library.rule_template import RuleTemplate

class RuleCHK0062(RuleTemplate):
    """
    CHK0062: Each specified biomedical concept is expected to be referenced by an activity.
    
    Applies to: Activity
    Attributes: biomedicalConcepts
    """
    
    def __init__(self):
        super().__init__("CHK0062", RuleTemplate.ERROR, "Each specified biomedical concept is expected to be referenced by an activity.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
