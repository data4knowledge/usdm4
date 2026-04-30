"""Tests for RuleDDF00229 — studyPhase against C66737 with M11 PT warning relaxation."""

from unittest.mock import MagicMock

from simple_error_log.errors import Errors
from usdm4.rules.library.rule_ddf00229 import (
    RuleDDF00229,
    _M11_TRIAL_PHASE_PTS,
)
from usdm4.rules.rule_template import RuleTemplate


# C66737 SDTM Trial Phase Response — minimal subset that lets us test
# the M11 PT relaxation. SDTM PTs are "Phase N Trial"; M11 PTs are
# "Phase N" (see _M11_TRIAL_PHASE_PTS in the rule module).
_SDTM_C66737 = [
    ("C15600", "Phase 1 Trial"),
    ("C15601", "Phase 2 Trial"),
    ("C15602", "Phase 3 Trial"),
    ("C48660", "Not Applicable"),
    ("C49686", "Phase IIa Trial"),  # USDM-only, no M11 alternate
]


def _ct_with(codes_decodes):
    ct = MagicMock()
    ct.klass_and_attribute.return_value = {
        "terms": [{"conceptId": c, "preferredTerm": d} for c, d in codes_decodes]
    }
    return ct


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


class TestRuleDDF00229Metadata:
    def test_metadata(self):
        rule = RuleDDF00229()
        assert rule._rule == "DDF00229"
        assert rule._level == RuleTemplate.ERROR


class TestRuleDDF00229Iteration:
    """Regression: previous implementation iterated only ObservationalStudyDesign,
    so InterventionalStudyDesign data was never validated."""

    def test_interventional_study_phase_is_validated(self):
        """An invalid Interventional studyPhase must produce a failure.

        Previously the rule body was `_ct_check(... "ObservationalStudyDesign" ...)`
        only, which meant an Interventional design with bad data passed silently.
        """
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
    """Pure CT-conformance behaviour — same shape as _ct_check."""

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


class TestRuleDDF00229M11Relaxation:
    """The new behaviour: M11 PT (e.g. 'Phase 1') for a code whose SDTM PT
    differs (e.g. 'Phase 1 Trial') is recorded as level=Warning, not Error."""

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
                        # Made-up decode; C49686 has no entry in _M11_TRIAL_PHASE_PTS.
                        "studyPhase": _alias_studyphase("C49686", "Phase IIa"),
                    }
                ]
            }
        )
        assert rule.validate({"data": data, "ct": ct}) is False
        entries = rule.errors().to_dict(level=Errors.DEBUG)
        assert len(entries) == 1
        assert entries[0]["level"] == "Error"


class TestRuleDDF00229M11Map:
    """Sanity checks on the hard-coded M11 PT map itself."""

    def test_m11_map_contains_all_eleven_phase_codes(self):
        """C217045 has 11 items per merged_elements.json (2025-11-16)."""
        assert len(_M11_TRIAL_PHASE_PTS) == 11

    def test_m11_map_keys_look_like_c_codes(self):
        for code in _M11_TRIAL_PHASE_PTS:
            assert code.startswith("C")
            assert code[1:].isdigit()
