from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0182(RuleTemplate):
    """
    CHK0182: Narrative content is expected to point to a child and/or to a content item text.
    
    Applies to: NarrativeContent
    Attributes: children, contentItem
    """
    
    def __init__(self):
        super().__init__("CHK0182", RuleTemplate.ERROR, "Narrative content is expected to point to a child and/or to a content item text.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
