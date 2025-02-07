from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class Rule00007(RuleTemplate):
    """
    DDF00007: If timing type is \"Fixed Reference\" then it must point to only one scheduled instance (e.g. attribute relativeToScheduledInstance must be equal to relativeFromScheduledInstance or it must be missing).
    
    Applies to: Timing
    Attributes: relativeToScheduledInstance
    """
    
    def __init__(self):
        super().__init__("DDF00007", RuleTemplate.ERROR, "If timing type is \"Fixed Reference\" then it must point to only one scheduled instance (e.g. attribute relativeToScheduledInstance must be equal to relativeFromScheduledInstance or it must be missing).")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
