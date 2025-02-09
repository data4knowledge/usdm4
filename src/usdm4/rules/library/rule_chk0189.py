from usdm3.rules.library.rule_template import RuleTemplate

class RuleCHK0189(RuleTemplate):
    """
    CHK0189: A study definition document version's status must be specifed using the status Value Set Terminology (C188723) DDF codelist.
    
    Applies to: StudyDefinitionDocumentVersion
    Attributes: status
    """
    
    def __init__(self):
        super().__init__("CHK0189", RuleTemplate.ERROR, "A study definition document version's status must be specifed using the status Value Set Terminology (C188723) DDF codelist.")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
