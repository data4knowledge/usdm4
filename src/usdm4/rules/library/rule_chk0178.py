from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0178(RuleTemplate):
    """
    CHK0178: An activity with children must not refer to a timeline, procedure, biomedical concept, biomedical concept category or biomedical concept surrogate.
    
    Applies to: Activity
    Attributes: children
    """
    
    def __init__(self):
        super().__init__("CHK0178", RuleTemplate.ERROR, "An activity with children must not refer to a timeline, procedure, biomedical concept, biomedical concept category or biomedical concept surrogate.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
