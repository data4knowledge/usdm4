from usdm4.rules.engine import RulesValidationEngine
from usdm4.base.singleton import Singleton


class RulesValidation4(metaclass=Singleton):
    def __init__(self, root_path: str):
        self.rules_validation = RulesValidationEngine(root_path, "usdm4.rules.library")

    def validate(self, filename: str):
        return self.rules_validation.validate_rules(filename)
