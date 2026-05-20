"""Invariants on the shared M11 trial-phase PT table.

The table is a hand-maintained mirror of M11 codelist C217045's
preferred-term column. These tests guard the basic shape; the
round-trip test in usdm4_protocol exercises the table end-to-end.
"""

from src.usdm4.assembler.m11_phase_aliases import M11_TRIAL_PHASE_PTS


def test_contains_all_eleven_phase_codes():
    """C217045 has 11 items per merged_elements.json (2025-11-16)."""
    assert len(M11_TRIAL_PHASE_PTS) == 11


def test_keys_look_like_nci_concept_codes():
    for code in M11_TRIAL_PHASE_PTS:
        assert code.startswith("C")
        assert code[1:].isdigit()


def test_values_are_non_empty_strings():
    for code, pt in M11_TRIAL_PHASE_PTS.items():
        assert isinstance(pt, str) and pt, f"{code} has empty PT"


def test_includes_both_m11_only_extension_codes():
    """C217024 and C217025 are the two codes M11 has but SDTM hasn't
    yet published; they must be in the alias table because the
    round-trip relies on them."""
    assert "C217024" in M11_TRIAL_PHASE_PTS
    assert "C217025" in M11_TRIAL_PHASE_PTS


def test_pts_use_m11_form_not_sdtm_form():
    """M11 PT for C15600 is 'Phase 1', not 'Phase I Trial' (SDTM form)."""
    assert M11_TRIAL_PHASE_PTS["C15600"] == "Phase 1"
    assert M11_TRIAL_PHASE_PTS["C15601"] == "Phase 2"
    assert M11_TRIAL_PHASE_PTS["C217024"] == "Phase 2/Phase 3/Phase 4"
