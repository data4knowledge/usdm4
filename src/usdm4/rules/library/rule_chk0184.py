from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0184(RuleTemplate):
    """
    CHK0184: If a section title is to be displayed then a title must be specified and vice versa.
    
    Applies to: NarrativeContent
    Attributes: sectionTitle, displaySectionTitle
    """
    
    def __init__(self):
        super().__init__("CHK0184", RuleTemplate.ERROR, "If a section title is to be displayed then a title must be specified and vice versa.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
