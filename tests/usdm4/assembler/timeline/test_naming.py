"""House-style names — issue 63, part 63.6.

Ported from ``test_timeline_assembler_name_collisions.py`` and the SAI-name
tests of the old ``test_timeline_assembler.py``, now against ``Naming``.

Names are cross-reference keys, so they have to be unique in the study. What
is pinned is that the SECOND claimant moves and the first does not: renaming
the holder would change the name of every epoch in every ordinary study for
the sake of the few that repeat one.
"""

import pytest

from src.usdm4.assembler.timeline import naming as naming_module
from src.usdm4.assembler.timeline.naming import Naming


@pytest.fixture
def naming():
    return Naming()


def epoch_name(naming: Naming, label: str, index: int = 1, t: int = 1) -> str:
    """The name the build stage gives this epoch."""
    return naming.claim_epoch_name(
        naming.qualify(naming.epoch_name(label, index), t), label
    )


class TestHouse:
    def test_loads_the_vocabulary(self, naming):
        assert naming.house()["activities"]["vital signs"] == "VS"

    def test_an_unreadable_file_degrades_to_generation(self, monkeypatch, tmp_path):
        monkeypatch.setattr(Naming, "_house_names", None)
        monkeypatch.setattr(naming_module, "_HOUSE_NAMES_PATH", tmp_path / "missing")
        assert Naming.house() == {}
        assert Naming().activity_name("Vital signs", 1) == "VS"  # generated


class TestQualify:
    def test_bare_in_a_single_timeline_study(self, naming):
        assert naming.qualify("E1", 2) == "E1"

    def test_prefixed_when_several_timelines(self, naming):
        naming.multi_timeline = True
        assert naming.qualify("E1", 2) == "T2-E1"


class TestKeys:
    def test_name_key_drops_case_punctuation_and_a_trailing_marker(self, naming):
        assert naming.name_key("Pregnancy Test") == "pregnancy test"
        assert naming.name_key("  Pregnancy test,12 ") == "pregnancy test"

    def test_identity_is_space_and_case_only(self, naming):
        assert naming.identity(" Cycle 1 ") == naming.identity("cycle 1")
        assert naming.identity("Cycle 1") != naming.identity("Cycle 2")
        assert naming.identity(None) == ""

    def test_initials(self, naming):
        assert naming.initials("Vital signs") == "VS"
        assert naming.initials("Haematology") == "HAEM"
        assert naming.initials("of the") == ""


class TestActivityNames:
    def test_curated_synonyms_do_not_collide(self, naming):
        """`adverse events` and `adverse event review` both curate to `AE`."""
        first = naming.activity_name("Adverse events", 1)
        second = naming.activity_name("Adverse event review", 2)
        assert first == "AE"
        assert second != first

    def test_the_first_claimant_keeps_the_curated_name(self, naming):
        naming.activity_name("Adverse event review", 1)
        assert naming.activity_name("Adverse events", 2) != "AE"

    def test_three_synonyms_are_all_distinct(self, naming):
        names = [
            naming.activity_name(text, index)
            for index, text in enumerate(
                ["Adverse events", "Adverse event review", "Adverse event"], 1
            )
        ]
        assert len(set(names)) == 3

    def test_the_same_label_keeps_its_name(self, naming):
        first = naming.activity_name("Adverse events", 1)
        assert naming.activity_name("Adverse events", 2) == first
        assert naming.activity_name("Adverse Events ", 3) == first

    def test_the_same_generated_label_keeps_its_name(self, naming):
        assert naming.activity_name("Blood draw", 1) == "BD"
        assert naming.activity_name("blood draw", 2) == "BD"

    def test_a_curated_name_taken_by_a_generated_one(self, naming):
        """`Alpha Elements` generates `AE` before anything curates to it."""
        assert naming.activity_name("Alpha Elements", 1) == "AE"
        assert naming.activity_name("Adverse events", 2) != "AE"

    def test_uncurated_activities(self, naming):
        assert naming.activity_name("Vital signs", 1) == "VS"
        assert naming.activity_name("CD4", 2) == "CD4"

    def test_a_trailing_footnote_letter_still_finds_the_curated_name(self, naming):
        assert naming.activity_name("Physical examinationb", 1) == "PE"

    def test_a_collision_extends_the_abbreviation(self, naming):
        assert naming.activity_name("Participant eligibility", 1) == "PE"
        assert naming.activity_name("Participant education", 2) == "PAED"

    def test_an_exhausted_extension_takes_a_number(self, naming):
        """Single-letter words cannot be extended, so the base takes an
        ordinal, and the next one along the next ordinal."""
        assert naming.activity_name("P E", 1) == "PE"
        assert naming.activity_name("P E.", 2) == "PE2"
        assert naming.activity_name("P E!", 3) == "PE3"

    @pytest.mark.parametrize("text", ["", "   ", None])
    def test_no_text_is_a_sequence_name(self, naming, text):
        assert naming.activity_name(text, 7) == "ACT7"

    def test_no_significant_words_is_a_sequence_name(self, naming):
        assert naming.activity_name("###", 4) == "ACT4"


class TestEpochNames:
    def test_two_screening_periods(self, naming):
        assert epoch_name(naming, "Period I - Screening", 1) == "SCR"
        assert epoch_name(naming, "Period II - Screening", 2) == "SCR2"

    def test_three_treatment_cycles(self, naming):
        names = [
            epoch_name(naming, label, index)
            for index, label in enumerate(
                [
                    "On-Treatment Cycle = 21 days",
                    "On-Treatment Cycle 2-n",
                    "On-Treatment Cycle 3-n",
                ],
                1,
            )
        ]
        assert names == ["TREAT", "TREAT2", "TREAT3"]

    def test_the_same_label_keeps_its_name(self, naming):
        assert epoch_name(naming, "Screening") == "SCR"
        assert epoch_name(naming, "Screening") == "SCR"

    def test_surrounding_space_and_case_are_the_same_epoch(self, naming):
        assert epoch_name(naming, "Follow-up") == "FU"
        assert epoch_name(naming, "  FOLLOW-UP ") == "FU"

    def test_a_trailing_number_is_not_the_same_epoch(self, naming):
        """`name_key` strips a trailing number — right for a house-name
        lookup, wrong for identity: `Cycle 1` and `Cycle 2` are two epochs."""
        assert epoch_name(naming, "Cycle 1", 1) != epoch_name(naming, "Cycle 2", 2)

    def test_timeline_qualification_keeps_names_apart(self, naming):
        naming.multi_timeline = True
        assert epoch_name(naming, "Screening", 1, t=1) == "T1-SCR"
        assert epoch_name(naming, "Screening", 1, t=2) == "T2-SCR"

    def test_a_repeat_within_one_timeline_still_moves(self, naming):
        naming.multi_timeline = True
        assert epoch_name(naming, "Period I - Screening", 1, t=2) == "T2-SCR"
        assert epoch_name(naming, "Period II - Screening", 2, t=2) == "T2-SCR2"

    def test_an_unmatched_label_generates_initials(self, naming):
        assert naming.epoch_name("Bone Marrow Substudy", 3) == "BMS"

    @pytest.mark.parametrize("label", ["", "   ", "###"])
    def test_no_usable_label_is_a_sequence_name(self, naming, label):
        assert naming.epoch_name(label, 3) == "EP3"


class TestSaiNames:
    def _names(self, naming, items, t=1):
        return [
            naming.sai_name(text, value, unit, visit, t, index)
            for index, (text, value, unit, visit) in enumerate(items)
        ]

    def test_from_day_week_cycle_text(self, naming):
        names = self._names(
            naming,
            [
                ("Day -42", -42, "day", None),
                ("Day 1", 1, "day", None),
                ("Week 12", 12, "week", None),
                ("Cycle 2 Day 1", None, None, None),
            ],
        )
        assert names == ["D-42", "D1", "W12", "C2D1"]

    def test_bare_numbers_take_the_unit_prefix_and_the_signed_value(self, naming):
        names = self._names(
            naming,
            [
                ("-2", -2, "week", None),
                ("0", 0, "week", None),
                ("42", -42, "day", None),
                ("7", None, "day", None),
                ("3", 3, "furlong", None),
            ],
        )
        assert names == ["W-2", "W0", "D-42", "D7", "3"]

    def test_visit_fallback_slug_and_dedupe(self, naming):
        names = self._names(
            naming,
            [
                (None, None, None, "Final Visit/ET"),
                ("", None, None, "A very long visit description indeed"),
                ("Day 1", 1, "day", None),
                ("Day 1", 1, "day", ""),
                (None, None, None, None),
                (None, None, None, ""),
            ],
        )
        assert names == [
            "FINAL VISIT ET",
            "A VERY LONG VISIT DE",
            "D1",
            "D1-2",
            "T1-SAI-5",
            "T1-SAI-6",
        ]

    def test_unusable_text_falls_through(self, naming):
        names = self._names(
            naming, [("###", None, None, "Day 5"), ("###", None, None, "")]
        )
        assert names == ["D5", "T1-SAI-2"]

    def test_a_single_cycle_names_from_cycle_and_day(self, naming):
        """Issue 66: the parsed cycle and day, whatever the text says."""
        assert naming.sai_name("D8", 8, "day", None, 1, 0, cycle=2) == "C2D8"
        assert naming.sai_name("Day -1", -1, "day", None, 1, 1, cycle=3) == "C3D-1"

    def test_a_cycle_without_a_day_timing_names_from_text(self, naming):
        assert naming.sai_name("Week 2", 2, "week", None, 1, 0, cycle=2) == "W2"
        assert naming.sai_name("Pre-dose", None, None, None, 1, 1, cycle=2) == (
            "PRE-DOSE"
        )

    def test_names_are_unique_across_timelines(self, naming):
        assert naming.sai_name("Day 1", 1, "day", None, 1, 0) == "D1"
        assert naming.sai_name("Day 1", 1, "day", None, 2, 0) == "D1-2"
