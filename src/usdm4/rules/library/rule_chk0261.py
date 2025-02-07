from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0261(RuleTemplate):
    """
    CHK0261: A study design's blinding schema must be specified according to the extensible Trial Blinding Schema Response (C66735) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).
    
    Applies to: InterventionalStudyDesign
    Attributes: blindingSchema
    """
    
    def __init__(self):
        super().__init__("CHK0261", RuleTemplate.ERROR, "A study design's blinding schema must be specified according to the extensible Trial Blinding Schema Response (C66735) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
