from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class Rule00016(RuleTemplate):
    """
    DDF00016: A specified condition for assessments must apply to at least to a procedure, biomedical concept, biomedical concept surrogate, biomedical concept category or a whole activity.
    
    Applies to: Condition
    Attributes: appliesTo
    """
    
    def __init__(self):
        super().__init__("DDF00016", RuleTemplate.ERROR, "A specified condition for assessments must apply to at least to a procedure, biomedical concept, biomedical concept surrogate, biomedical concept category or a whole activity.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
