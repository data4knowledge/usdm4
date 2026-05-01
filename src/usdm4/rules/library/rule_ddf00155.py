from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00155(RuleTemplate):
    """
    DDF00155: For CDISC codelist references (where the code system is 'http://www.cdisc.org'), the code system version must be a valid CDISC terminology release date in ISO 8601 date format.

    Applies to: Code
    Attributes: codeSystemVersion
    """

    # Known CDISC terminology release dates. The CT library exposes the
    # subset that is actually loaded in this run via ``effective_dates()``;
    # we union the loaded set with this historical list so the rule
    # accepts any legitimate CDISC release without forcing every protocol
    # to be re-issued against the latest cache. Extend this list when CDISC
    # publishes a new terminology package (the dynamic CT side will catch
    # most cases automatically; this list backstops the historical ones).
    HISTORICAL_VERSIONS: frozenset[str] = frozenset(
        {
            "2020-03-27",
            "2020-05-08",
            "2020-06-26",
            "2020-09-25",
            "2020-11-06",
            "2020-12-18",
            "2021-03-26",
            "2021-06-25",
            "2021-09-24",
            "2021-12-17",
            "2022-03-25",
            "2022-06-24",
            "2022-09-30",
            "2022-12-16",
            "2023-03-31",
            "2023-06-30",
            "2023-09-29",
            "2023-12-15",
            "2024-03-29",
            "2024-09-27",
            "2025-03-28",
            "2026-03-27",
        }
    )

    def __init__(self):
        super().__init__(
            "DDF00155",
            RuleTemplate.ERROR,
            "For CDISC codelist references (where the code system is 'http://www.cdisc.org'), the code system version must be a valid CDISC terminology release date in ISO 8601 date format.",
        )

    def validate(self, config: dict) -> bool:
        ct = config.get("ct")
        loaded = (
            ct.effective_dates()
            if ct is not None and hasattr(ct, "effective_dates")
            else set()
        )
        # Hybrid lookup: a version is valid if it's loaded in the current
        # CT cache OR is a known historical CDISC release date. The CT
        # side keeps the rule forward-compatible (new releases are picked
        # up automatically); the historical list keeps the rule from
        # rejecting legitimate older protocols.
        valid_versions = loaded | self.HISTORICAL_VERSIONS
        data = config["data"]
        items = data.instances_by_klass("Code")
        for item in items:
            if "codeSystem" in item and item["codeSystem"] == "http://www.cdisc.org":
                if "codeSystemVersion" not in item:
                    self._add_failure(
                        "Missing codeSystemVersion",
                        "Code",
                        "codeSystemVersion",
                        data.path_by_id(item["id"]),
                    )
                else:
                    if item["codeSystemVersion"] not in valid_versions:
                        self._add_failure(
                            "Invalid codeSystemVersion",
                            "Code",
                            "codeSystemVersion",
                            data.path_by_id(item["id"]),
                        )
        return self._result()
