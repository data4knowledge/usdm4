from usdm3.rules.library.rule_ddf00105 import RuleDDF00105 as V3Rule


class RuleDDF00105(V3Rule):
    def validate(self, config: dict) -> bool:
        print("USDM 4 105")
        return self._validate(
            config, ["InterventionalStudyDesign", "ObservationalStudyDesign"]
        )
