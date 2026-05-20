"""Tests for RuleDDF00229 — studyPhase against C66737 with M11 PT warning relaxation.

The rule routes membership through the common Library predicate
(``has_codelist`` + ``find_in_codelist``). These tests stub the CT
library with a small FakeCT replicating the predicate surface — no
real Library instance is constructed.
"""

from unittest.mock import MagicMock

from simple_error_log.errors import Errors
from usdm4.rules.library.rule_ddf00229 import RuleDDF00229
from usdm4.rules.rule_template import RuleTemplate


# C66737 SDTM Trial Phase Response — minimal subset that exercises the
# M11 PT relaxation. SDTM PTs are "Phase N Trial"; M11 PTs are "Phase N".
_SDTM_C66737 = [
    {"conceptId": "C15600", "preferredTerm": "Phase 1 Trial", "submissionValue": "PHASE I TRIAL"},
    {"conceptId": "C15601", "preferredTerm": "Phase 2 Trial", "submissionValue": "PHASE II TRIAL"},
    {"conceptId": "C15602", "preferredTerm": "Phase 3 Trial", "submissionValue": "PHASE III TRIAL"},
    {"conceptId": "C48660", "preferredTerm": "Not Applicable", "submissionValue": "NOT APPLICABLE"},
    # C49686 ("Phase IIa Trial") is in SDTM but NOT in M11's C217045 —
    # used to prove "no M11 fallback for SDTM-only codes".
    {"conceptId": "C49686", "preferredTerm": "Phase IIa Trial", "submissionValue": "PHASE IIA TRIAL"},
]


class FakeCT:
    """In-memory CT stub mirroring Library.has_codelist + find_in_codelist."""

    def __init__(self, codelists: dict[str, list[dict]]):
        self._codelists = codelists

    def has_codelist(self, codelist_id: str) -> bool:
        return codelist_id in self._codelists

    def find_in_codelist(
        self, value: str, codelist_id: str, by: str = "any"
    ) -> tuple[dict, str]:
        if codelist_id not in self._codelists:
            return (None, None)
        needle = (value or "").casefold()
        for term in self._codelists[codelist_id]:
            if by in ("concept_id", "any") and term.get("conceptId", "") == value:
                return (term, term.get("source") or "cdisc")
            if by in ("preferred_term", "any") and (
                term.get("preferredTerm") or ""
            ).casefold() == needle:
                return (term, term.get("source") or "cdisc")
            if by in ("submission_value", "any") and (
                term.get("submissionValue") or ""
            ).casefold() == needle:
                return (term, term.get("source") or "cdisc")
        return (None, None)


def _ct_with(terms):
    return FakeCT({"C66737": list(terms)})


def _data_for(instances_by_klass):
    data = MagicMock()
    data.instances_by_klass.side_effect = lambda k: instances_by_klass.get(k, [])
    data.path_by_id.return_value = "$.path"
    return data


def _alias_studyphase(code, decode):
    """Build the AliasCode-shaped studyPhase entry the corpus uses."""
    return {
        "id": "AliasCode_X",
        "standardCode": {"code": code, "decode": decode},
    }


def _plain_studyphase(code, decode):
    """Build the plain Code-shaped studyPhase entry."""
    return {"id": "Code_X", "code": code, "decode": decode}


class TestRuleDDF00229Metadata:
    def test_metadata(self):
        rule = RuleDDF00229()
        assert rule._rule == "DDF00229"
        assert rule._level == RuleTemplate.ERROR


class TestRuleDDF00229Iteration:
    """Regression: previous implementation iterated only ObservationalStudyDesign,
    so InterventionalStudyDesign data was never validated."""

    def test_interventional_study_phase_is_validated(self):
        """An invalid Interventional studyPhase must produce a failure."""
        rule = RuleDDF00229()
        ct = _ct_with(_SDTM_C66737)
        data = _data_for(
            {
                "InterventionalStudyDesign": [
                    {"id": "I1", "studyPhase": _alias_studyphase("BAD", "BAD")}
                ]
            }
        )
        assert rule.validate({"data": data, "ct": ct}) is False
        assert rule.errors().count() >= 1

    def test_observational_study_phase_is_still_validated(self):
        rule = RuleDDF00229()
        ct = _ct_with(_SDTM_C66737)
        data = _data_for(
            {
                "ObservationalStudyDesign": [
                    {"id": "O1", "studyPhase": _alias_studyphase("BAD", "BAD")}
                ]
            }
        )
        assert rule.validate({"data": data, "ct": ct}) is False

    def test_no_designs_no_findings(self):
        rule = RuleDDF00229()
        ct = _ct_with(_SDTM_C66737)
        data = _data_for({})
        assert rule.validate({"data": data, "ct": ct}) is True


class TestRuleDDF00229Codelist:
    """Pure CT-conformance behaviour."""

    def test_sdtm_pt_passes(self):
        """code=C15600 + decode='Phase 1 Trial' is the SDTM PT — pass."""
        rule = RuleDDF00229()
        ct = _ct_with(_SDTM_C66737)
        data = _data_for(
            {
                "InterventionalStudyDesign": [
                    {
                        "id": "I1",
                        "studyPhase": _alias_studyphase("C15600", "Phase 1 Trial"),
                    }
                ]
            }
        )
        assert rule.validate({"data": data, "ct": ct}) is True

    def test_sdtm_submission_value_passes(self):
        """decode matching submissionValue (the SDTM submission string) is also valid."""
        rule = RuleDDF00229()
        ct = _ct_with(_SDTM_C66737)
        data = _data_for(
            {
                "InterventionalStudyDesign": [
                    {
                        "id": "I1",
                        "studyPhase": _alias_studyphase("C15600", "PHASE I TRIAL"),
                    }
                ]
            }
        )
        assert rule.validate({"data": data, "ct": ct}) is True

    def test_plain_code_shape_validates(self):
        """studyPhase as a plain Code (no standardCode wrapper) also validates."""
        rule = RuleDDF00229()
        ct = _ct_with(_SDTM_C66737)
        data = _data_for(
            {
                "InterventionalStudyDesign": [
                    {
                        "id": "I1",
                        "studyPhase": _plain_studyphase("C15600", "Phase 1 Trial"),
                    }
                ]
            }
        )
        assert rule.validate({"data": data, "ct": ct}) is True

    def test_invalid_code_is_error(self):
        rule = RuleDDF00229()
        ct = _ct_with(_SDTM_C66737)
        data = _data_for(
            {
                "InterventionalStudyDesign": [
                    {
                        "id": "I1",
                        "studyPhase": _alias_studyphase("BAD", "Phase 1 Trial"),
                    }
                ]
            }
        )
        assert rule.validate({"data": data, "ct": ct}) is False
        entries = rule.errors().to_dict(level=Errors.DEBUG)
        assert len(entries) == 1
        assert entries[0]["level"] == "Error"

    def test_invalid_code_and_decode_is_single_error(self):
        rule = RuleDDF00229()
        ct = _ct_with(_SDTM_C66737)
        data = _data_for(
            {
                "InterventionalStudyDesign": [
                    {
                        "id": "I1",
                        "studyPhase": _alias_studyphase("BAD", "BAD"),
                    }
                ]
            }
        )
        assert rule.validate({"data": data, "ct": ct}) is False
        entries = rule.errors().to_dict(level=Errors.DEBUG)
        assert len(entries) == 1
        assert "neither" in entries[0]["message"].lower()

    def test_code_decode_mismatch_pair_is_error(self):
        """Valid code C15600 + valid (but for a different code) decode is a pair mismatch."""
        rule = RuleDDF00229()
        ct = _ct_with(_SDTM_C66737)
        data = _data_for(
            {
                "InterventionalStudyDesign": [
                    {
                        "id": "I1",
                        # Code is Phase 1, decode is the Phase 2 PT.
                        "studyPhase": _alias_studyphase("C15600", "Phase 2 Trial"),
                    }
                ]
            }
        )
        assert rule.validate({"data": data, "ct": ct}) is False
        entries = rule.errors().to_dict(level=Errors.DEBUG)
        assert len(entries) == 1
        assert "do not match" in entries[0]["message"]

    def test_missing_attribute_is_error(self):
        rule = RuleDDF00229()
        ct = _ct_with(_SDTM_C66737)
        data = _data_for({"InterventionalStudyDesign": [{"id": "I1"}]})
        assert rule.validate({"data": data, "ct": ct}) is False
        msgs = [e["message"] for e in rule.errors().to_dict(level=Errors.DEBUG)]
        assert any("Missing attribute" in m for m in msgs)

    def test_null_studyphase_is_silent(self):
        """An explicitly-null studyPhase is a legitimate empty value."""
        rule = RuleDDF00229()
        ct = _ct_with(_SDTM_C66737)
        data = _data_for(
            {"InterventionalStudyDesign": [{"id": "I1", "studyPhase": None}]}
        )
        assert rule.validate({"data": data, "ct": ct}) is True


class TestRuleDDF00229CodelistMissing:
    """When C66737 isn't loaded, skip rather than fail everything (cache-stale tolerance)."""

    def test_codelist_not_loaded_skips_rule(self):
        rule = RuleDDF00229()
        ct = FakeCT({})  # C66737 absent
        data = MagicMock()
        assert rule.validate({"data": data, "ct": ct}) is True
        data.instances_by_klass.assert_not_called()


class TestRuleDDF00229M11Relaxation:
    """The M11 PT (e.g. 'Phase 1') for a code whose SDTM PT differs (e.g. 'Phase 1 Trial')
    is recorded as level=Warning, not Error. M11 PT data lives in the shared
    M11_TRIAL_PHASE_PTS module (see usdm4.assembler.m11_phase_aliases)."""

    def test_m11_pt_emits_warning_not_error(self):
        rule = RuleDDF00229()
        ct = _ct_with(_SDTM_C66737)
        data = _data_for(
            {
                "InterventionalStudyDesign": [
                    {
                        "id": "I1",
                        # M11 PT for C15600 is "Phase 1" (SDTM PT is "Phase 1 Trial").
                        "studyPhase": _alias_studyphase("C15600", "Phase 1"),
                    }
                ]
            }
        )
        # Rule still reports Failure (any finding fails the rule), but the
        # entry must be at WARNING level, not ERROR.
        assert rule.validate({"data": data, "ct": ct}) is False
        entries = rule.errors().to_dict(level=Errors.DEBUG)
        assert len(entries) == 1
        entry = entries[0]
        assert entry["level"] == "Warning"
        assert "M11" in entry["message"] or "CPT" in entry["message"]
        assert "'Phase 1 Trial'" in entry["message"]  # SDTM PT reported in message

    def test_unknown_decode_for_valid_code_is_still_error(self):
        """A typo decode that is neither SDTM PT nor M11 PT must stay ERROR."""
        rule = RuleDDF00229()
        ct = _ct_with(_SDTM_C66737)
        data = _data_for(
            {
                "InterventionalStudyDesign": [
                    {
                        "id": "I1",
                        "studyPhase": _alias_studyphase("C15600", "Phaze 1"),
                    }
                ]
            }
        )
        assert rule.validate({"data": data, "ct": ct}) is False
        entries = rule.errors().to_dict(level=Errors.DEBUG)
        assert len(entries) == 1
        assert entries[0]["level"] == "Error"

    def test_decode_for_code_not_in_m11_is_error(self):
        """C49686 ('Phase IIa Trial') exists in SDTM but not in M11. A
        non-SDTM decode for it must remain ERROR — no M11 fallback."""
        rule = RuleDDF00229()
        ct = _ct_with(_SDTM_C66737)
        data = _data_for(
            {
                "InterventionalStudyDesign": [
                    {
                        "id": "I1",
                        # C49686 has no entry in M11_TRIAL_PHASE_PTS.
                        "studyPhase": _alias_studyphase("C49686", "Phase IIa"),
                    }
                ]
            }
        )
        assert rule.validate({"data": data, "ct": ct}) is False
        entries = rule.errors().to_dict(level=Errors.DEBUG)
        assert len(entries) == 1
        assert entries[0]["level"] == "Error"


class TestRuleDDF00229Extensions:
    """Once C217024/C217025 are loaded into C66737 via the extension
    mechanism, DDF00229 should treat them as first-class members. This
    proves the predicate seam delivers on the design intent."""

    def test_extension_code_with_extension_pt_passes(self):
        """C217024 (loaded as extension to C66737) with SDTM-form decode passes."""
        rule = RuleDDF00229()
        c66737_with_extensions = _SDTM_C66737 + [
            {
                "conceptId": "C217024",
                "preferredTerm": "Phase II/III/IV Trial",
                "submissionValue": "",
                "source": "NCIt-M11",  # tagged by Library._merge_extension
            },
        ]
        ct = _ct_with(c66737_with_extensions)
        data = _data_for(
            {
                "InterventionalStudyDesign": [
                    {
                        "id": "I1",
                        "studyPhase": _alias_studyphase(
                            "C217024", "Phase II/III/IV Trial"
                        ),
                    }
                ]
            }
        )
        assert rule.validate({"data": data, "ct": ct}) is True
        assert rule.errors().count() == 0

    def test_extension_code_with_m11_pt_emits_warning(self):
        """C217024 with M11-form decode 'Phase 2/Phase 3/Phase 4' → warning."""
        rule = RuleDDF00229()
        c66737_with_extensions = _SDTM_C66737 + [
            {
                "conceptId": "C217024",
                "preferredTerm": "Phase II/III/IV Trial",
                "submissionValue": "",
                "source": "NCIt-M11",
            },
        ]
        ct = _ct_with(c66737_with_extensions)
        data = _data_for(
            {
                "InterventionalStudyDesign": [
                    {
                        "id": "I1",
                        "studyPhase": _alias_studyphase(
                            "C217024", "Phase 2/Phase 3/Phase 4"
                        ),
                    }
                ]
            }
        )
        assert rule.validate({"data": data, "ct": ct}) is False
        entries = rule.errors().to_dict(level=Errors.DEBUG)
        assert len(entries) == 1
        assert entries[0]["level"] == "Warning"
