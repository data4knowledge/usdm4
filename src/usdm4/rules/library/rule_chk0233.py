from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0233(RuleTemplate):
    """
    CHK0233: Every study role must apply to either a study version or at least one study design, but not both.
    
    Applies to: StudyRole
    Attributes: appliesTo
    """
    
    def __init__(self):
        super().__init__("CHK0233", RuleTemplate.ERROR, "Every study role must apply to either a study version or at least one study design, but not both.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
