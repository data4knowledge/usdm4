from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class Rule00089(RuleTemplate):
    """
    DDF00089: Any parameter name referenced in a tag in the text should be specified in the data dictionary parameter maps.
    
    Applies to: EligibilityCriterion, Characteristic, Condition, Objective, Endpoint
    Attributes: text
    """
    
    def __init__(self):
        super().__init__("DDF00089", RuleTemplate.ERROR, "Any parameter name referenced in a tag in the text should be specified in the data dictionary parameter maps.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
