from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class RuleCHK0275(RuleTemplate):
    """
    CHK0275: If a biospecimen retention indicates that a type of biospecimen is retained, then there must be an indication of whether the type of biospecimen includes DNA.
    
    Applies to: BiospecimenRetention
    Attributes: includesDNA
    """
    
    def __init__(self):
        super().__init__("CHK0275", RuleTemplate.ERROR, "If a biospecimen retention indicates that a type of biospecimen is retained, then there must be an indication of whether the type of biospecimen includes DNA.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
