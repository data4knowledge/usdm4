from usdm3.rules.library.rule_template import RuleTemplate

class RuleCHK0242(RuleTemplate):
    """
    CHK0242: Each study definition document version is expected to be referenced by either a study version or a study design.
    
    Applies to: StudyVersion, ObservationalStudyDesign, InterventionalStudyDesign
    Attributes: documentVersions
    """
    
    def __init__(self):
        super().__init__("CHK0242", RuleTemplate.ERROR, "Each study definition document version is expected to be referenced by either a study version or a study design.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
