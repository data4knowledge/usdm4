from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0231(RuleTemplate):
    """
    CHK0231: Narrative content item text is expected to be HTML formatted.
    
    Applies to: NarrativeContentItem
    Attributes: text
    """
    
    def __init__(self):
        super().__init__("CHK0231", RuleTemplate.ERROR, "Narrative content item text is expected to be HTML formatted.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
