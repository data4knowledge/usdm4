from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class Rule00021(RuleTemplate):
    """
    DDF00021: An instance of a class must not refer to itself as its previous instance.
    
    Applies to: StudyEpoch, Encounter, Activity, NarrativeContent, EligibilityCriterion, StudyAmendment
    Attributes: previous
    """
    
    def __init__(self):
        super().__init__("DDF00021", RuleTemplate.ERROR, "An instance of a class must not refer to itself as its previous instance.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
