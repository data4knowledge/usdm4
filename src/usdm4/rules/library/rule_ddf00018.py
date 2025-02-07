from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class Rule00018(RuleTemplate):
    """
    DDF00018: An instance of a class must not reference itself as one of its own children.
    
    Applies to: BiomedicalConceptCategory, StudyProtocolDocumentVersion, StudyDefinitionDocumentVersion, NarrativeContent, Activity
    Attributes: children
    """
    
    def __init__(self):
        super().__init__("DDF00018", RuleTemplate.ERROR, "An instance of a class must not reference itself as one of its own children.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
