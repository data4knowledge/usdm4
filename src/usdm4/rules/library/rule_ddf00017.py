from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class Rule00017(RuleTemplate):
    """
    DDF00017: Within subject enrollment, the quantity must be a number or a percentage (i.e. the unit must be empty or %).
    
    Applies to: SubjectEnrollment
    Attributes: quantity
    """
    
    def __init__(self):
        super().__init__("DDF00017", RuleTemplate.ERROR, "Within subject enrollment, the quantity must be a number or a percentage (i.e. the unit must be empty or %).")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
