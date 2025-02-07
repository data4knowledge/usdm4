from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0271(RuleTemplate):
    """
    CHK0271: An interventional study must be specified using the InterventionalStudyDesign class. 
    
    Applies to: InterventionalStudyDesign
    Attributes: studyType
    """
    
    def __init__(self):
        super().__init__("CHK0271", RuleTemplate.ERROR, "An interventional study must be specified using the InterventionalStudyDesign class. ")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
