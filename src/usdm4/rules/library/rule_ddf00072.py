from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class Rule00072(RuleTemplate):
    """
    DDF00072: A study cell must only reference an epoch that is defined within the same study design as the study cell.
    
    Applies to: StudyCell
    Attributes: epoch
    """
    
    def __init__(self):
        super().__init__("DDF00072", RuleTemplate.ERROR, "A study cell must only reference an epoch that is defined within the same study design as the study cell.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
