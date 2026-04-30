# MANUAL: do not regenerate
#
# DDF00229: study phase must be the SDTM Trial Phase Response (C66737)
# codelist (extensible). Two important deviations from the generic
# _ct_check pattern that the previous implementation didn't capture:
#
# 1) The rule applies to BOTH InterventionalStudyDesign and
#    ObservationalStudyDesign. The previous implementation only iterated
#    Observational, so on the protocol_corpus run (n=234, all
#    Interventional) the rule passed vacuously while CORE caught 222
#    real decode-mismatch findings. Same shape of bug as the original
#    DDF00141 (which has since been fixed).
#
# 2) Cross-standard PT mismatches between CDISC SDTM C66737 and ICH
#    M11 / TransCelerate CPT C217045 are not data-quality bugs — they
#    reflect the difference between the M11 protocol-template
#    vocabulary and the SDTM submission vocabulary. The same NCI
#    concept (e.g. C15600) is "Phase 1" in M11 but "Phase 1 Trial" in
#    SDTM. We surface those as level=Warning rather than level=Error
#    so callers can filter them out of the "real errors" view.
#
# Source for the M11 preferred terms below:
#   ../m11_specification/m11_versions/2025-11-16/output_data/merged_elements.json
#   path: $["Trial Phase"]["technical"]["ct"]["items"][*]
# Refresh by re-extracting from a newer M11 version's merged_elements.json
# when one becomes available.
from simple_error_log.errors import Errors

from usdm4.rules.rule_template import RuleTemplate, ValidationLocation


# M11 / CPT codelist C217045 "Trial Phase" — c_code → preferred term.
# These PTs are accepted by DDF00229 as level=Warning when the
# corresponding C-code is valid in SDTM C66737 but the data uses the
# M11 PT instead of the SDTM PT.
_M11_TRIAL_PHASE_PTS: dict[str, str] = {
    "C54721": "Early Phase 1",
    "C15600": "Phase 1",
    "C15693": "Phase 1/Phase 2",
    "C198366": "Phase 1/Phase 2/Phase 3",
    "C198367": "Phase 1/Phase 3",
    "C15601": "Phase 2",
    "C15694": "Phase 2/Phase 3",
    "C217024": "Phase 2/Phase 3/Phase 4",
    "C15602": "Phase 3",
    "C217025": "Phase 3/Phase 4",
    "C15603": "Phase 4",
}


_DESIGN_KLASSES: tuple[str, ...] = (
    "InterventionalStudyDesign",
    "ObservationalStudyDesign",
)


class RuleDDF00229(RuleTemplate):
    """
    DDF00229: A study design's study phase must be specified according to the extensible Trial Phase Response (C66737) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: ObservationalStudyDesign, InterventionalStudyDesign
    Attributes: studyPhase
    """

    def __init__(self):
        super().__init__(
            "DDF00229",
            RuleTemplate.ERROR,
            "A study design's study phase must be specified according to the extensible Trial Phase Response (C66737) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        ct = config["ct"]
        for klass in _DESIGN_KLASSES:
            instances = data.instances_by_klass(klass)
            if not instances:
                continue
            codes, decodes = self._check_codelist(ct, klass, "studyPhase")
            for instance in instances:
                self._check_one(instance, klass, codes, decodes, data)
        return self._result()

    def _check_one(
        self,
        instance: dict,
        klass: str,
        codes: list[str],
        decodes: list[str],
        data,
    ) -> None:
        path = data.path_by_id(instance["id"])
        if "studyPhase" not in instance:
            self._add_failure("Missing attribute", klass, "studyPhase", path)
            return
        item = instance["studyPhase"]
        if not isinstance(item, dict):
            # null or non-dict: legitimate empty value, nothing to validate
            return

        # AliasCode shape: studyPhase.standardCode carries code/decode.
        # Plain Code shape: code/decode are on the item itself.
        target = item
        if isinstance(item.get("standardCode"), dict):
            target = item["standardCode"]
        code = target.get("code")
        decode = target.get("decode")
        code_index = self._find_index(codes, code)
        decode_index = self._find_index(decodes, decode)

        if code_index is None and decode_index is None:
            self._add_failure(
                f"Invalid code and decode '{code}' and '{decode}', "
                "neither the code and decode are in the codelist",
                klass,
                "studyPhase",
                path,
            )
            return
        if code_index is None:
            self._add_failure(
                f"Invalid code '{code}', the code is not in the codelist",
                klass,
                "studyPhase",
                path,
            )
            return
        if decode_index is None:
            # Code is in C66737 but decode isn't its SDTM PT.
            # If the decode matches the M11 PT for this code, treat as a
            # cross-standard difference (warning); otherwise error.
            sdtm_pt = decodes[code_index]
            m11_pt = _M11_TRIAL_PHASE_PTS.get(code)
            if m11_pt is not None and decode == m11_pt:
                self._add_at_level(
                    f"Decode '{decode}' for code '{code}' uses the "
                    f"M11/CPT preferred term; SDTM C66737 PT is "
                    f"'{sdtm_pt}'",
                    klass,
                    "studyPhase",
                    path,
                    Errors.WARNING,
                )
            else:
                self._add_failure(
                    f"Invalid decode '{decode}', the decode is not in the codelist",
                    klass,
                    "studyPhase",
                    path,
                )
            return
        if code_index != decode_index:
            self._add_failure(
                f"Invalid code and decode pair '{code}' and '{decode}', "
                "the code and decode do not match",
                klass,
                "studyPhase",
                path,
            )

    def _add_at_level(
        self,
        message: str,
        klass: str,
        attribute: str,
        path: str,
        level: int,
    ) -> None:
        """Record a finding at an explicit severity level (overriding self._level)."""
        location = ValidationLocation(
            self._rule, self._rule_text, klass, attribute, path
        )
        self._errors.add(message, location, self._rule, level)
