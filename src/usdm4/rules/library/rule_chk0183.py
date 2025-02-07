from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0183(RuleTemplate):
    """
    CHK0183: If a section number is to be displayed then a number must be specified and vice versa.
    
    Applies to: NarrativeContent
    Attributes: sectionNumber, displaySectionNumber
    """
    
    def __init__(self):
        super().__init__("CHK0183", RuleTemplate.ERROR, "If a section number is to be displayed then a number must be specified and vice versa.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
