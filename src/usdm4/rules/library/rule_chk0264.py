from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0264(RuleTemplate):
    """
    CHK0264: Within a study design, if more sub types are defined, they must be distinct.
    
    Applies to: InterventionalStudyDesign, ObservationalStudyDesign
    Attributes: subTypes
    """
    
    def __init__(self):
        super().__init__("CHK0264", RuleTemplate.ERROR, "Within a study design, if more sub types are defined, they must be distinct.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
