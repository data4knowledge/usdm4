from usdm3.rules.library.rule_template import RuleTemplate
from usdm3.rules.library.rule_ddfsdw001 import RuleDDFSDW001 as V3Rule
from usdm4.__version__ import __model_version__ as model_version


class RuleDDFSDW001(V3Rule):
    def __init__(self):
        super().__init__()
        self._rule_text = "The version in the wrapper should be set to 3.12.0"

    def validate(self, config: dict) -> bool:
        print(f"MODEL VERSIOn: {model_version}")
        return self._validate_version(config, model_version)
