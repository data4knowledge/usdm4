from usdm3.rules.library.rule_template import RuleTemplate

class RuleCHK0214(RuleTemplate):
    """
    CHK0214: A reference identifier type must be specified according to the extensible reference identifier type (Cxxx) DDF codelist  (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).
    
    Applies to: ReferenceIdentifier
    Attributes: type
    """
    
    def __init__(self):
        super().__init__("CHK0214", RuleTemplate.ERROR, "A reference identifier type must be specified according to the extensible reference identifier type (Cxxx) DDF codelist  (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
