from usdm3.rules.library.rule_template import RuleTemplate

class RuleCHK0188(RuleTemplate):
    """
    CHK0188: A piece of narrative content must only reference narrative content items that have been defined within the study version as the narrative content.
    
    Applies to: NarrativeContent
    Attributes: contentItem
    """
    
    def __init__(self):
        super().__init__("CHK0188", RuleTemplate.ERROR, "A piece of narrative content must only reference narrative content items that have been defined within the study version as the narrative content.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
