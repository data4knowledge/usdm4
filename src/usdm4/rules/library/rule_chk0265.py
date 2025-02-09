from usdm3.rules.library.rule_template import RuleTemplate

class RuleCHK0265(RuleTemplate):
    """
    CHK0265: Within a study design, if more therapeutic areas are defined, they must be distinct.
    
    Applies to: InterventionalStudyDesign, ObservationalStudyDesign
    Attributes: therapeuticAreas
    """
    
    def __init__(self):
        super().__init__("CHK0265", RuleTemplate.ERROR, "Within a study design, if more therapeutic areas are defined, they must be distinct.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
