from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0246(RuleTemplate):
    """
    CHK0246: The sponsor study role must point to exactly one organization.
    
    Applies to: StudyRole
    Attributes: organizations
    """
    
    def __init__(self):
        super().__init__("CHK0246", RuleTemplate.ERROR, "The sponsor study role must point to exactly one organization.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
