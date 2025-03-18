from usdm3.rules.library.rule_ddfsdw001 import RuleDDFSDW001 as V3Rule
from usdm4.__version__ import __model_version__ as model_version


class RuleDDF00155(V3Rule):
    def validate(self, config: dict) -> bool:
        return self._validate_version(config, model_version)
