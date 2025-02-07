from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0234(RuleTemplate):
    """
    CHK0234: A study role must not reference both assigned persons and organizations.
    
    Applies to: StudyRole
    Attributes: assignedPersons, organizations
    """
    
    def __init__(self):
        super().__init__("CHK0234", RuleTemplate.ERROR, "A study role must not reference both assigned persons and organizations.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
