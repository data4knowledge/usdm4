# MANUAL: do not regenerate
#
# Implication: if BiospecimenRetention.isRetained is True then
# includesDNA must be an explicit bool (True or False), not None.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00231(RuleTemplate):
    """
    DDF00231: If a biospecimen retention indicates that a type of biospecimen is retained, then there must be an indication of whether the type of biospecimen includes DNA.

    Applies to: BiospecimenRetention
    Attributes: isRetained, includesDNA
    """

    def __init__(self):
        super().__init__(
            "DDF00231",
            RuleTemplate.ERROR,
            "If a biospecimen retention indicates that a type of biospecimen is retained, then there must be an indication of whether the type of biospecimen includes DNA.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for retention in data.instances_by_klass("BiospecimenRetention"):
            if retention.get("isRetained") is not True:
                continue
            if retention.get("includesDNA") not in (True, False):
                self._add_failure(
                    "BiospecimenRetention.isRetained is True but includesDNA is not set to True or False",
                    "BiospecimenRetention",
                    "isRetained, includesDNA",
                    data.path_by_id(retention["id"]),
                )
        return self._result()
