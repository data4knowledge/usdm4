from usdm3.rules.library.rule_ddf00106 import RuleDDF00106 as V3Rule


class RuleDDF00106(V3Rule):

    def validate(self, config: dict) -> bool:
        print("USDM 4 106")
        return self._validate(config, ["InterventionalStudyDesign", "ObservationalStudyDesign"])
