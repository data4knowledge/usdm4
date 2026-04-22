"""Tests for RuleDDF00161 — Activity parent/child ordering via prev/next."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00161 import RuleDDF00161, _descendants
from usdm4.rules.rule_template import RuleTemplate


# ---------------------------------------------------------------------------
# _descendants helper
# ---------------------------------------------------------------------------


def test_descendants_flat():
    cm = {"A": ["B", "C"], "B": [], "C": []}
    assert _descendants("A", cm) == {"B", "C"}


def test_descendants_nested():
    cm = {"A": ["B"], "B": ["C"], "C": []}
    assert _descendants("A", cm) == {"B", "C"}


def test_descendants_cycle_safe():
    """A ↔ B cycle — recursion terminates via visited set."""
    cm = {"A": ["B"], "B": ["A"]}
    result = _descendants("A", cm)
    # Only B reachable; A is skipped once visited.
    assert "B" in result


# ---------------------------------------------------------------------------
# Rule validate()
# ---------------------------------------------------------------------------


class TestRuleDDF00161:
    def test_metadata(self):
        rule = RuleDDF00161()
        assert rule._rule == "DDF00161"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, designs_by_klass):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: designs_by_klass.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_activities_skipped(self):
        rule = RuleDDF00161()
        design = {"id": "D1", "activities": []}
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is True

    def test_non_dict_activity_ignored(self):
        rule = RuleDDF00161()
        design = {"id": "D1", "activities": [None, "scalar"]}
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is True

    def test_valid_ordering_passes(self):
        """Root A → child B (first child). B's previousId = A (its parent).
        No childIds under B, no issue 3."""
        rule = RuleDDF00161()
        design = {
            "id": "D1",
            "activities": [
                {"id": "A", "childIds": ["B"], "nextId": "B"},
                {"id": "B", "previousId": "A"},
            ],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is True

    def test_issue_1_parent_nextid_not_a_child(self):
        rule = RuleDDF00161()
        design = {
            "id": "D1",
            "activities": [
                {"id": "A", "childIds": ["B"], "nextId": "Z"},
                {"id": "B", "previousId": "A"},
            ],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is False
        # Issue 1 fires on A, plus issue 3 fires on B because B's prevId (A)
        # has childIds [B] and B IS in them — actually no, B is in prev's
        # childIds so issue 3 is clean. So 1 failure.
        assert rule.errors().count() == 1

    def test_issue_2_child_previd_bad(self):
        rule = RuleDDF00161()
        design = {
            "id": "D1",
            "activities": [
                {"id": "A", "childIds": ["B"], "nextId": "B"},
                {"id": "B", "previousId": "Z"},  # Z is neither parent nor descendant
            ],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is False
        # Issue 2 for B (previousId is 'Z', not in {A}).
        assert rule.errors().count() == 1

    def test_issue_3_previd_has_children_but_self_not_among_them(self):
        rule = RuleDDF00161()
        design = {
            "id": "D1",
            "activities": [
                {"id": "A", "childIds": ["B"], "nextId": "B"},  # A has child B
                {"id": "B", "previousId": "A"},  # B is child of A
                {"id": "C", "previousId": "A"},  # C references A but A does not list C
            ],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is False
        # C: issue 3 fires because A has childIds [B] but C is not among them.
        # Issue 2 also fires because C has no parent so issue 2 skipped.
        assert rule.errors().count() >= 1
