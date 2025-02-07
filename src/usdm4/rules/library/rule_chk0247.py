from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0247(RuleTemplate):
    """
    CHK0247: The sponsor study role must be applicable to a study version.
    
    Applies to: StudyRole
    Attributes: appliesTo
    """
    
    def __init__(self):
        super().__init__("CHK0247", RuleTemplate.ERROR, "The sponsor study role must be applicable to a study version.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
