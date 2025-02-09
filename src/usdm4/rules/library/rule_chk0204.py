from usdm3.rules.library.rule_template import RuleTemplate

class RuleCHK0204(RuleTemplate):
    """
    CHK0204: An administrable product property type must be specified according to the extensible administrable property type (Cxxxx) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).
    
    Applies to: AdministrableProductProperty
    Attributes: type
    """
    
    def __init__(self):
        super().__init__("CHK0204", RuleTemplate.ERROR, "An administrable product property type must be specified according to the extensible administrable property type (Cxxxx) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
