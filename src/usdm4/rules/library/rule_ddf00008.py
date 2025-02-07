from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class Rule00008(RuleTemplate):
    """
    DDF00008: A scheduled activity instance must refer to either a default condition or a timeline exit, but not both.
    
    Applies to: ScheduledActivityInstance
    Attributes: timelineExit, defaultCondition
    """
    
    def __init__(self):
        super().__init__("DDF00008", RuleTemplate.ERROR, "A scheduled activity instance must refer to either a default condition or a timeline exit, but not both.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
