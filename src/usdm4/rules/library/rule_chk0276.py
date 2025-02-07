from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0276(RuleTemplate):
    """
    CHK0276: An observational study (including patient registries) is expected to have a study phase decode value of \"NOT APPLICABLE\".
    
    Applies to: ObservationalStudyDesign
    Attributes: studyPhase
    """
    
    def __init__(self):
        super().__init__("CHK0276", RuleTemplate.ERROR, "An observational study (including patient registries) is expected to have a study phase decode value of \"NOT APPLICABLE\".")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
