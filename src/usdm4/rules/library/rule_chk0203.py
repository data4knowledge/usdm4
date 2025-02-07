from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0203(RuleTemplate):
    """
    CHK0203: An administrable dose form must be specfied according to the extensible Pharmaceutical Dosage Form (C66726) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).
    
    Applies to: AdministrableProduct
    Attributes: administrableDoseForm
    """
    
    def __init__(self):
        super().__init__("CHK0203", RuleTemplate.ERROR, "An administrable dose form must be specfied according to the extensible Pharmaceutical Dosage Form (C66726) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
