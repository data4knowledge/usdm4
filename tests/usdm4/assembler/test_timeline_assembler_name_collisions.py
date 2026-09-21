"""Names are cross-reference keys, so they have to be unique in the study.

Two of the three naming paths could hand back a name already in use. The
curated activity branch returned its `house_names.yaml` entry as it stood, and
that file maps synonyms onto one name on purpose -- `adverse events` and
`adverse event review` both ask for `AE`. Epoch names come from the CT epoch
terms, which are many-to-one in the same way: two screening periods, or three
treatment cycles, all resolve to one term. `Builder.create` raises on the
duplicate and the failure propagates until the study itself comes back None,
so a single repeated name costs the whole document rather than the one entity
that collided.

What is pinned here is that the SECOND claimant moves and the first does not.
Renaming the holder would change the name of every epoch in every ordinary
study for the sake of the few that repeat one.
"""

import os
import pathlib

import pytest
from simple_error_log.errors import Errors

from src.usdm4.assembler.timeline_assembler import TimelineAssembler
from src.usdm4.builder.builder import Builder


def root_path():
    base = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


@pytest.fixture(scope="module")
def builder():
    return Builder(root_path(), Errors())


@pytest.fixture
def assembler(builder):
    builder.clear()
    return TimelineAssembler(builder, Errors())


def epoch_name(assembler, label, index=1, t=1):
    """The name `_add_epochs` would give this epoch."""
    return assembler._claim_epoch_name(
        assembler._qualify(assembler._epoch_name(label, index), t), label
    )


class TestActivityNames:
    def test_curated_synonyms_do_not_collide(self, assembler):
        """`adverse events` and `adverse event review` both curate to `AE`."""
        first = assembler._activity_name("Adverse events", 1)
        second = assembler._activity_name("Adverse event review", 2)
        assert first == "AE"
        assert second != first

    def test_the_first_claimant_keeps_the_curated_name(self, assembler):
        assembler._activity_name("Adverse event review", 1)
        assert assembler._activity_name("Adverse events", 2) != "AE"

    def test_three_synonyms_are_all_distinct(self, assembler):
        names = [
            assembler._activity_name(text, index)
            for index, text in enumerate(
                ["Adverse events", "Adverse event review", "Adverse event"], 1
            )
        ]
        assert len(set(names)) == 3

    def test_the_same_label_keeps_its_name(self, assembler):
        first = assembler._activity_name("Adverse events", 1)
        assert assembler._activity_name("Adverse events", 2) == first

    def test_a_curated_name_taken_by_a_generated_one(self, assembler):
        """`Alpha Elements` generates `AE` before anything curates to it."""
        assert assembler._activity_name("Alpha Elements", 1) == "AE"
        assert assembler._activity_name("Adverse events", 2) != "AE"

    def test_uncurated_activities_are_unaffected(self, assembler):
        assert assembler._activity_name("Vital signs", 1) == "VS"
        assert assembler._activity_name("CD4", 2) == "CD4"


class TestEpochNames:
    def test_two_screening_periods(self, assembler):
        assert epoch_name(assembler, "Period I - Screening", 1) == "SCR"
        assert epoch_name(assembler, "Period II - Screening", 2) == "SCR2"

    def test_three_treatment_cycles(self, assembler):
        names = [
            epoch_name(assembler, label, index)
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

    def test_the_same_label_keeps_its_name(self, assembler):
        assert epoch_name(assembler, "Screening", 1) == "SCR"
        assert epoch_name(assembler, "Screening", 1) == "SCR"

    def test_a_single_phase_study_is_unchanged(self, assembler):
        """No ordinal anywhere when nothing repeats -- the holder never moves."""
        assert epoch_name(assembler, "Screening", 1) == "SCR"
        assert epoch_name(assembler, "Follow-up", 2) == "FU"

    def test_timeline_qualification_keeps_names_apart(self, assembler):
        """`T1-SCR` and `T2-SCR` are already distinct; neither gains an ordinal."""
        assembler._multi_timeline = True
        assert epoch_name(assembler, "Screening", 1, t=1) == "T1-SCR"
        assert epoch_name(assembler, "Screening", 1, t=2) == "T2-SCR"

    def test_a_repeat_within_one_timeline_still_moves(self, assembler):
        assembler._multi_timeline = True
        assert epoch_name(assembler, "Period I - Screening", 1, t=2) == "T2-SCR"
        assert epoch_name(assembler, "Period II - Screening", 2, t=2) == "T2-SCR2"


class TestSameThingAskingTwice:
    """Two epochs and one epoch claimed twice are different situations.

    Only a genuinely different epoch is given another name. The same one
    asking again gets its own name back, so the builder refuses it exactly as
    it does today -- that is a fault upstream and should stay loud, not be
    quietly resolved into a second epoch the protocol never had.
    """

    def test_the_same_label_is_not_renamed(self, assembler):
        assert epoch_name(assembler, "Screening") == "SCR"
        assert epoch_name(assembler, "Screening") == "SCR"

    def test_surrounding_space_and_case_are_the_same_epoch(self, assembler):
        assert epoch_name(assembler, "Follow-up") == "FU"
        assert epoch_name(assembler, "  FOLLOW-UP ") == "FU"

    def test_a_trailing_number_is_not_the_same_epoch(self, assembler):
        """`_name_key` strips a trailing number, which is right for looking a
        house name up and wrong for identity -- `Cycle 1` and `Cycle 2` are two
        epochs and must not be collapsed into one."""
        first = epoch_name(assembler, "Cycle 1", 1)
        second = epoch_name(assembler, "Cycle 2", 2)
        assert first != second

    def test_the_same_activity_is_not_renamed(self, assembler):
        assert assembler._activity_name("Adverse events", 1) == "AE"
        assert assembler._activity_name("Adverse Events ", 2) == "AE"


class TestAddEpochs:
    """The collision through the real path, where it aborted the build."""

    def _data(self, labels):
        return {
            "epochs": {"items": [{"text": label} for label in labels]},
            "timepoints": {
                "items": [
                    {
                        "index": str(i),
                        "text": f"Day {i + 1}",
                        "value": str(i + 1),
                        "unit": "days",
                    }
                    for i in range(len(labels))
                ]
            },
        }

    def test_colliding_epochs_are_both_created(self, assembler):
        data = self._data(["Period I - Screening", "Period II - Screening"])
        epochs = assembler._add_epochs(data)
        assert len(epochs) == 2
        assert [epoch.name for epoch in epochs] == ["SCR", "SCR2"]
        assert [epoch.label for epoch in epochs] == [
            "Period I - Screening",
            "Period II - Screening",
        ]

    def test_a_trailing_space_is_the_same_epoch_not_a_second_one(self, assembler):
        """A repeated header cell differing by a stray space is one epoch."""
        data = self._data(["Screening", "Screening ", "Treatment"])
        epochs = assembler._add_epochs(data)
        assert [epoch.name for epoch in epochs] == ["SCR", "TREAT"]

    def test_non_colliding_epochs_are_untouched(self, assembler):
        data = self._data(["Screening", "Treatment", "Follow-up"])
        epochs = assembler._add_epochs(data)
        assert [epoch.name for epoch in epochs] == ["SCR", "TREAT", "FU"]
