"""Tests for RuleDDF00025 — no window on anchor (Fixed Reference) Timing.

Regression context (corpus run, n=234):

- The previous body matched timings via ``type.decode == "Fixed Reference"``,
  but the corpus stores ``"Fixed Reference Timing Type"`` (the SDTM PT for
  C201358). The decode filter never matched, so the rule reported 0
  findings on every file while CORE caught 103 violations on
  ``windowLabel``. The rule now matches on ``type.code == "C201358"``.

- The previous body only checked ``windowLower`` and ``windowUpper``;
  the docstring said the rule applies to ``windowLabel`` too. The body
  now checks all three.

- Empty strings on the window-* attributes are not treated as "defined"
  (they appear in the corpus on non-flagged files and CORE matches
  that interpretation). We use ``bool(value)``.
"""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00025 import RuleDDF00025
from usdm4.rules.rule_template import RuleTemplate


_FR_TYPE = {"code": "C201358", "decode": "Fixed Reference Timing Type"}
_AFTER_TYPE = {"code": "C201356", "decode": "After Timing Type"}


class TestRuleDDF00025:
    def _data(self, timings):
        data = MagicMock()
        data.instances_by_klass.return_value = timings
        data.path_by_id.return_value = "$.path"
        return data

    def test_metadata(self):
        rule = RuleDDF00025()
        assert rule._rule == "DDF00025"
        assert rule._level == RuleTemplate.ERROR

    # ---- filter: anchor selection -----------------------------------------

    def test_non_anchor_timing_is_skipped(self):
        """A non-Fixed-Reference timing is not subject to this rule."""
        rule = RuleDDF00025()
        data = self._data([{"id": "T1", "type": _AFTER_TYPE, "windowLabel": "+/- 1d"}])
        assert rule.validate({"data": data}) is True

    def test_filter_uses_code_not_decode(self):
        """A wrong-decode shape with the right code still triggers the rule.

        Regression: previous filter was ``decode == "Fixed Reference"``, which
        missed the actual SDTM PT ``"Fixed Reference Timing Type"`` (and is
        fragile to any wording variation). Match by code.
        """
        rule = RuleDDF00025()
        data = self._data(
            [
                {
                    "id": "T1",
                    # Code is canonical; decode is whatever the data
                    # extractor wrote — the rule must match by code.
                    "type": {"code": "C201358", "decode": "anything goes"},
                    "windowLabel": "+/- 1d",
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_decode_only_no_code_is_skipped(self):
        """A timing with the old decode but no code field is not matched.

        Defensive: we used to over-match on the decode string. The rule
        now relies on the code, so a decode-only entry is ignored rather
        than being treated as Fixed Reference.
        """
        rule = RuleDDF00025()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": {"decode": "Fixed Reference"},  # no code
                    "windowLabel": "+/- 1d",
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_missing_type_block_is_skipped(self):
        """A timing with no type block must not crash the rule."""
        rule = RuleDDF00025()
        data = self._data([{"id": "T1", "windowLabel": "+/- 1d"}])
        assert rule.validate({"data": data}) is True

    # ---- body: which window attributes are checked ------------------------

    def test_anchor_no_window_passes(self):
        rule = RuleDDF00025()
        data = self._data([{"id": "T1", "type": _FR_TYPE}])
        assert rule.validate({"data": data}) is True

    def test_anchor_with_window_label_fails(self):
        """Regression: previous body did not check windowLabel at all.

        On the protocol_corpus run, this was the only attribute CORE
        ever flagged on (windowLower/Upper were always empty strings).
        """
        rule = RuleDDF00025()
        data = self._data([{"id": "T1", "type": _FR_TYPE, "windowLabel": "+/- 1d"}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_anchor_with_window_lower_fails(self):
        rule = RuleDDF00025()
        data = self._data([{"id": "T1", "type": _FR_TYPE, "windowLower": "PT1H"}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_anchor_with_window_upper_fails(self):
        rule = RuleDDF00025()
        data = self._data([{"id": "T1", "type": _FR_TYPE, "windowUpper": "PT2H"}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_anchor_with_all_three_window_attrs_fails_three_times(self):
        rule = RuleDDF00025()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": _FR_TYPE,
                    "windowLabel": "+/- 1d",
                    "windowLower": "PT1H",
                    "windowUpper": "PT2H",
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 3

    # ---- empty-string handling --------------------------------------------

    def test_empty_string_window_attrs_are_not_defined(self):
        """An empty-string windowLower/Upper/Label is treated as 'not set'.

        This matches CORE's behaviour on the corpus (131 Fixed Reference
        timings had windowLower=windowUpper="" with no windowLabel and
        CORE did not flag any of them).
        """
        rule = RuleDDF00025()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": _FR_TYPE,
                    "windowLabel": "",
                    "windowLower": "",
                    "windowUpper": "",
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_none_window_attrs_pass(self):
        rule = RuleDDF00025()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": _FR_TYPE,
                    "windowLabel": None,
                    "windowLower": None,
                    "windowUpper": None,
                }
            ]
        )
        assert rule.validate({"data": data}) is True
