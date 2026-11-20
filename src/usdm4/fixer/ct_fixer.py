from collections import Counter

from usdm4.ct.cdisc.library import Library, MissingCodelistError
from usdm4.fixer.fix_result import FixResult
from usdm4.fixer.walk import instances, super_classes
from usdm4.rules.library.rule_ddf00155 import RuleDDF00155

STEP = "ct"
CDISC = "http://www.cdisc.org"

# CDISC terminology release dates as DDF00155 accepts them; the loaded
# cache dates are added at run time.
RELEASES = RuleDDF00155.HISTORICAL_VERSIONS


class CTFixer:
    """Align CDISC codes with the CT package, without changing any code.

    Version: every Code with codeSystem CDISC whose codeSystemVersion is
    missing or not a CDISC release date gets the release date most used in
    the file (the CT cache date if none is valid). A valid date is left
    alone, so the file never ends up with mixed versions (DDF00073).

    Decode: only a Code on an attribute mapped to a codelist in
    ``ct_config.yaml`` is looked at (an AliasCode through its standardCode).
    If the code is in that codelist, decode is set to the preferred term
    unless it already equals the preferred term or the submission value. If
    the code is not in the codelist, or codeSystem is not CDISC, it is
    reported and left alone.
    """

    def __init__(self, result: FixResult, library: Library):
        self._result = result
        self._library = library

    def fix(self) -> None:
        found = instances(self._result.data)
        self._fix_versions(found)
        for instance in found:
            for attribute, value in instance.node.items():
                if not isinstance(value, (dict, list)):
                    continue
                codelist = self._codelist(
                    instance.klass, attribute, f"{instance.path}.{attribute}"
                )
                if codelist is None:
                    continue
                path = f"{instance.path}.{attribute}"
                if isinstance(value, dict):
                    self._fix_code(value, path, instance.klass, attribute, codelist)
                else:
                    for index, item in enumerate(value):
                        if isinstance(item, dict):
                            self._fix_code(
                                item,
                                f"{path}[{index}]",
                                instance.klass,
                                attribute,
                                codelist,
                            )

    def _fix_versions(self, found: list) -> None:
        valid = RELEASES | self._library.effective_dates()
        codes = [
            i for i in found if i.klass == "Code" and i.node.get("codeSystem") == CDISC
        ]
        used = Counter(
            i.node.get("codeSystemVersion")
            for i in codes
            if i.node.get("codeSystemVersion") in valid
        )
        if used:
            target, reason = used.most_common(1)[0][0], "release date most used in file"
        else:
            target, reason = max(self._library.effective_dates()), "CT cache date"
        for instance in codes:
            version = instance.node.get("codeSystemVersion")
            if version in valid:
                continue
            self._result.change(
                STEP,
                f"{instance.path}.codeSystemVersion",
                "Code",
                "codeSystemVersion",
                version,
                target,
                f"not a CDISC release date; {reason}",
            )
            instance.node["codeSystemVersion"] = target

    def _codelist(self, klass: str, attribute: str, path: str) -> dict | None:
        for candidate in super_classes(klass):
            try:
                codelist = self._library.klass_and_attribute(candidate, attribute)
            except MissingCodelistError as e:
                self._result.issue(STEP, path, klass, attribute, None, str(e))
                return None
            if codelist is not None:
                return codelist
        return None

    def _fix_code(
        self, code: dict, path: str, klass: str, attribute: str, codelist: dict
    ) -> None:
        if code.get("instanceType") == "AliasCode":
            code = code.get("standardCode")
            path = f"{path}.standardCode"
            if not isinstance(code, dict):
                return
        if code.get("instanceType") != "Code":
            return
        cl_id = codelist.get("conceptId")
        term = next(
            (t for t in codelist["terms"] if t.get("conceptId") == code.get("code")),
            None,
        )
        if term is None:
            self._result.issue(
                STEP,
                path,
                klass,
                attribute,
                code.get("code"),
                f"code {code.get('code')!r} ({code.get('decode')!r}) is not in "
                f"codelist {cl_id}; left unchanged",
            )
            return
        if "source" not in term and code.get("codeSystem") != CDISC:
            self._result.issue(
                STEP,
                path,
                klass,
                attribute,
                code.get("codeSystem"),
                f"codeSystem {code.get('codeSystem')!r} is not {CDISC!r} for "
                f"CDISC code {code.get('code')!r}; left unchanged",
            )
        preferred = term.get("preferredTerm")
        allowed = {preferred, term.get("submissionValue")}
        if preferred and code.get("decode") not in allowed:
            self._result.change(
                STEP,
                f"{path}.decode",
                "Code",
                "decode",
                code.get("decode"),
                preferred,
                f"preferred term of {code.get('code')} in codelist {cl_id}",
            )
            code["decode"] = preferred
