import os
import pathlib
from usdm3.rules.library.rule_ddf00082 import RuleDDF00082 as V3Rule

class RuleDDF00082(V3Rule):

    def _schema_path(self) -> str:
        print(f"Schema path: {pathlib.Path(__file__).parent.resolve()}")
        root = pathlib.Path(__file__).parent.resolve()
        return os.path.join(root, "schema/usdm_v3-6.json")
