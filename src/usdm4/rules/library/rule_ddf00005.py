from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class Rule00005(RuleTemplate):
    """
    DDF00005: Every study version must have exactly one study identifier with an identifier scope that references a clinical study sponsor organization.
    
    Applies to: StudyIdentifier
    Attributes: studyIdentifierScope
    """
    
    def __init__(self):
        super().__init__("DDF00005", RuleTemplate.ERROR, "Every study version must have exactly one study identifier with an identifier scope that references a clinical study sponsor organization.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
