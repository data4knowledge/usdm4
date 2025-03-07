import os
import json
import pathlib
from usdm4.rules.rules_validation import RulesValidation
from usdm3.rules.rules_validation_results import RulesValidationResults
from usdm4.api.wrapper import Wrapper
from usdm4.convert.convert import Convert
from usdm4.minimum.minimum import Minimum


class USDM4:
    def validate(self, file_path: str) -> RulesValidationResults:
        path = self._library_path()
        validator = RulesValidation(path, "usdm4.rules.library")
        return validator.validate_rules(file_path)

    def convert(self, file_path: str) -> Wrapper:
        with open(file_path, "r") as file:
            data = json.load(file)
        return Convert.convert(data)

    def minimum(self, study_name: str, sponsor_id: str, version: str) -> Wrapper:
        return Minimum.minimum(study_name, sponsor_id, version)

    def _library_path(self) -> str:
        root = pathlib.Path(__file__).parent.resolve()
        return os.path.join(root, "rules/library")
