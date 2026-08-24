"""Tests for the shared Fixed Reference Timing predicate."""

from usdm4.rules.timing import FIXED_REFERENCE_CODE, is_fixed_reference


class TestIsFixedReference:
    def test_matches_on_code(self):
        assert is_fixed_reference({"type": {"code": FIXED_REFERENCE_CODE}}) is True

    def test_code_wins_over_unrecognised_decode(self):
        assert (
            is_fixed_reference(
                {"type": {"code": FIXED_REFERENCE_CODE, "decode": "anything"}}
            )
            is True
        )

    def test_decode_alone_is_not_enough(self):
        """No decode fallback: preferred terms drift, codes do not."""
        assert (
            is_fixed_reference({"type": {"decode": "Fixed Reference Timing Type"}})
            is False
        )
        assert is_fixed_reference({"type": {"decode": "Fixed Reference"}}) is False

    def test_other_timing_type_is_not_fixed(self):
        assert (
            is_fixed_reference(
                {"type": {"code": "C201356", "decode": "After Timing Type"}}
            )
            is False
        )

    def test_missing_type_block(self):
        assert is_fixed_reference({"id": "T1"}) is False

    def test_type_block_not_a_dict(self):
        assert is_fixed_reference({"type": None}) is False
        assert is_fixed_reference({"type": "Fixed Reference"}) is False

    def test_timing_not_a_dict(self):
        assert is_fixed_reference(None) is False
        assert is_fixed_reference("Timing") is False
