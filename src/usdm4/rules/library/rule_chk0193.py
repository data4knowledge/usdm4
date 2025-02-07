from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0193(RuleTemplate):
    """
    CHK0193: There must be exactly one sponsor study identifier (i.e., a study identifier whose scope is an organization that is identified as the organization for the sponsor study role).
    
    Applies to: StudyIdentifier
    Attributes: scope
    """
    
    def __init__(self):
        super().__init__("CHK0193", RuleTemplate.ERROR, "There must be exactly one sponsor study identifier (i.e., a study identifier whose scope is an organization that is identified as the organization for the sponsor study role).")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
