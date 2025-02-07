from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0241(RuleTemplate):
    """
    CHK0241: A study definition document version must not be referenced more than once by the same study design.
    
    Applies to: ObservationalStudyDesign, InterventionalStudyDesign
    Attributes: documentVersions
    """
    
    def __init__(self):
        super().__init__("CHK0241", RuleTemplate.ERROR, "A study definition document version must not be referenced more than once by the same study design.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
