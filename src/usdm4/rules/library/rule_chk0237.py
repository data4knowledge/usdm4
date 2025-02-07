from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0237(RuleTemplate):
    """
    CHK0237: A masking is expected to be defined for at least one study role in a study design with a blinding schema that is not open label or double blind.
    
    Applies to: StudyRole
    Attributes: masking
    """
    
    def __init__(self):
        super().__init__("CHK0237", RuleTemplate.ERROR, "A masking is expected to be defined for at least one study role in a study design with a blinding schema that is not open label or double blind.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
