# MANUAL: do not regenerate
#
# DDF00229: study phase must be the SDTM Trial Phase Response (C66737)
# codelist (extensible). Two deviations from the generic _ct_check
# pattern that the previous implementation didn't capture:
#
# 1) The rule applies to BOTH InterventionalStudyDesign and
#    ObservationalStudyDesign. An earlier implementation only iterated
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
# Consolidation note (CT-extensions design): membership checks now
# route through the common Library predicate (`find_in_codelist`) — the
# single seam every CT-checking rule uses. The M11 PT table that
# powers the warning relaxation lives in
# `usdm4.assembler.m11_phase_aliases`, shared with the M11Decoder so
# the two no longer drift. See `project_m11_sdtm_phase_code_tension`
# memory for the full design context.
#
# Missing-codelist contract: if C66737 is not loaded, the Library
# predicate raises MissingCodelistError. We let it propagate; the rule
# engine surfaces it as a per-rule EXCEPTION outcome so the operator
# sees the config flaw rather than a misleading "rule passed". See
# feedback_missing_codelist_must_raise.
from simple_error_log.errors import Errors

from usdm4.assembler.m11_phase_aliases import M11_TRIAL_PHASE_PTS
from usdm4.rules.rule_template import RuleTemplate, ValidationLocation


_C66737 = "C66737"

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
        # No cache-stale guard here: C66737 is a baseline SDTM codelist
        # that must always be loaded. If it isn't, the first
        # find_in_codelist call raises MissingCodelistError and the
        # rule engine logs it as an exception outcome — the operator
        # sees the config flaw immediately rather than every studyPhase
        # silently marked valid.
        for klass in _DESIGN_KLASSES:
            for instance in data.instances_by_klass(klass):
                self._check_one(instance, klass, ct, data)
        return self._result()

    def _check_one(self, instance: dict, klass: str, ct, data) -> None:
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

        code_term, _ = ct.find_in_codelist(code, _C66737, by="concept_id")
        decode_term, _ = (
            ct.find_in_codelist(decode, _C66737, by="any")
            if decode is not None
            else (None, None)
        )

        if code_term is None and decode_term is None:
            self._add_failure(
                f"Invalid code and decode '{code}' and '{decode}', "
                "neither the code and decode are in the codelist",
                klass,
                "studyPhase",
                path,
            )
            return
        if code_term is None:
            self._add_failure(
                f"Invalid code '{code}', the code is not in the codelist",
                klass,
                "studyPhase",
                path,
            )
            return
        if decode_term is None:
            # Code is in C66737 but decode isn't its SDTM PT or SV.
            # If the decode matches the M11 PT for this code, treat as a
            # cross-standard difference (warning); otherwise error.
            sdtm_pt = code_term.get("preferredTerm", code)
            m11_pt = M11_TRIAL_PHASE_PTS.get(code)
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
        if code_term.get("conceptId") != decode_term.get("conceptId"):
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
