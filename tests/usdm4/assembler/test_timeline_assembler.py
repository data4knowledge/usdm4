"""The timeline assembler, end to end — issue 63, part 63.6.

Rewritten against the new input (``ScheduleTimelineInput``) and the parse →
plan → build structure. The behaviour pinned here is the behaviour the old
tests pinned, reached through ``execute`` instead of private methods; naming,
parsing and planning have their own tests in ``tests/usdm4/assembler/timeline``.
Today's defects that later rules fix are pinned as they are, and say so.
Issue 65 (R4, timing without cycles) fixed the timing ones.
"""

import types

import pytest
from simple_error_log.errors import Errors

from src.usdm4.api.extensions_d4k import (
    TLF_EXT_URL,
    TLO_EXT_URL,
    TLP_EXT_URL,
    TLU_EXT_URL,
)
from src.usdm4.assembler import timeline_assembler as timeline_assembler_module
from src.usdm4.assembler.timeline_assembler import TimelineAssembler
from src.usdm4.builder.builder import Builder
from src.usdm4.expander.timepoint import Timepoint
from tests.usdm4.assembler.timeline.helpers import (
    activity,
    column,
    root_path,
    simple,
    timeline,
    value,
)


@pytest.fixture(scope="module")
def builder():
    return Builder(root_path(), Errors())


@pytest.fixture
def errors():
    return Errors()


@pytest.fixture
def assembler(builder, errors):
    builder.clear()
    return TimelineAssembler(builder, errors)


def messages(errors: Errors) -> list[str]:
    return [item["message"] for item in errors.to_dict(0)]


def timing_types(tl) -> list[str]:
    return [t.type.decode.replace(" Timing Type", "") for t in tl.timings]


# ----------------------------------------------------------------------
# State and dispatch


class TestState:
    def test_starts_empty(self, assembler):
        assert assembler.timelines == []
        assert assembler.epochs == []
        assert assembler.encounters == []
        assert assembler.activities == []
        assert assembler.conditions == []
        assert assembler.biomedical_concepts == []
        assert assembler.biomedical_concept_surrogates == []

    def test_clear_resets_everything(self, assembler):
        assembler.execute([simple()])
        assert assembler.timelines
        assembler.clear()
        assert assembler.timelines == []
        assert assembler.epochs == []
        assert assembler.encounters == []
        assert assembler.activities == []
        assert assembler.conditions == []


class TestDispatch:
    @pytest.mark.parametrize("data", [None, []])
    def test_nothing_in_nothing_out(self, assembler, data):
        assembler.execute(data)
        assert assembler.timelines == []

    def test_a_single_dict_is_a_list_of_one(self, assembler):
        assembler.execute(simple())
        assert [t.name for t in assembler.timelines] == ["TIMELINE-1"]

    def test_an_outer_failure_is_caught_and_reported(
        self, assembler, errors, monkeypatch
    ):
        def boom(*args, **kwargs):
            raise RuntimeError("double link failed")

        monkeypatch.setattr(assembler._builder, "double_link", boom)
        assembler.execute([simple()])
        assert any("creation of study design" in m for m in messages(errors))

    def test_a_timeline_that_fails_to_build_adds_nothing(
        self, assembler, errors, monkeypatch
    ):
        class Boom:
            def __init__(self, *args, **kwargs):
                pass

            def build(self):
                raise RuntimeError("build failed")

        monkeypatch.setattr(timeline_assembler_module, "TimelineBuild", Boom)
        assembler.execute([simple()])
        assert assembler.timelines == []
        assert assembler.epochs == []
        assert any("creation of timeline 1" in m for m in messages(errors))


# ----------------------------------------------------------------------
# Timelines


class TestTimelines:
    def test_minimal_timeline(self, assembler):
        assembler.execute([simple()])
        (tl,) = assembler.timelines
        assert tl.mainTimeline is True
        assert tl.name == "TIMELINE-1"
        assert tl.label == "Main timeline"
        assert tl.description == "The main timeline"
        assert len(tl.instances) == 2
        assert tl.entryId == tl.instances[0].id
        assert len(assembler.epochs) == 2
        assert len(assembler.encounters) == 2
        assert [a.label for a in assembler.activities] == ["Consent", "Blood Draw"]

    def test_the_chain_runs_column_to_column_and_ends_at_the_exit(self, assembler):
        assembler.execute([simple()])
        (tl,) = assembler.timelines
        first, last = tl.instances
        assert first.defaultConditionId == last.id
        assert first.timelineExitId is None
        assert last.defaultConditionId is None
        assert last.timelineExitId == tl.exits[0].id

    def test_several_timelines_exactly_one_main(self, assembler):
        assembler.execute([simple(), simple("profile"), simple("unclassified")])
        assert [t.name for t in assembler.timelines] == [
            "TIMELINE-1",
            "TIMELINE-2",
            "TIMELINE-3",
        ]
        assert [t.mainTimeline for t in assembler.timelines] == [True, False, False]

    def test_main_chosen_by_type_regardless_of_order(self, assembler):
        assembler.execute([simple("profile"), simple("main")])
        assert [t.mainTimeline for t in assembler.timelines] == [False, True]

    def test_no_main_type_falls_back_to_the_first(self, assembler):
        assembler.execute([simple("arm"), simple("cohort")])
        assert [t.mainTimeline for t in assembler.timelines] == [True, False]

    def test_labels_and_descriptions(self, assembler):
        assembler.execute(
            [
                simple(description="The whole schedule"),
                simple("profile", title="PK sampling"),
            ]
        )
        main, sub = assembler.timelines
        assert (main.label, main.description) == ("Main timeline", "The whole schedule")
        assert (sub.label, sub.description) == ("PK sampling", "Subsidiary timeline 2")

    def test_default_subsidiary_label(self, assembler):
        assembler.execute([simple(), simple("unclassified")])
        assert assembler.timelines[1].label == "Timeline 2"

    def test_entry_condition_is_still_hard_coded(self, assembler):
        """Design § 8 — out of scope for issue 63, pinned until fixed. R6
        leaves every non-conditional family on it."""
        assembler.execute([simple()])
        assert assembler.timelines[0].entryCondition == "Paricipant identified"


class TestConditionalTimelines:
    """R6 (#70): a conditional timeline is a sibling timeline entered on its
    printed entry condition, else on a default from its type (U4-29)."""

    CONDITIONAL = ["unscheduled", "early_termination", "adverse_event"]

    def test_every_conditional_type_has_a_default(self):
        from src.usdm4.assembler.schema.schedule_timeline_schema import FAMILY
        from src.usdm4.assembler.timeline.build import TimelineBuild

        conditional = {t for t, f in FAMILY.items() if f == "conditional"}
        assert set(TimelineBuild.CONDITIONAL_ENTRY_CONDITIONS) == conditional

    @pytest.mark.parametrize("type", CONDITIONAL)
    def test_printed_entry_condition_is_used(self, assembler, errors, type):
        text = "Participant discontinues study treatment"
        assembler.execute([simple(), simple(type, entry_condition=text)])
        assert assembler.timelines[1].entryCondition == text
        assert not any("no entry condition" in m for m in messages(errors))

    def test_printed_entry_condition_is_trimmed(self, assembler):
        assembler.execute(
            [simple(), simple("unscheduled", entry_condition="  If needed \n")]
        )
        assert assembler.timelines[1].entryCondition == "If needed"

    @pytest.mark.parametrize(
        "type, default",
        [
            ("unscheduled", "Unscheduled visit"),
            ("early_termination", "Early termination"),
            ("adverse_event", "Adverse event"),
        ],
    )
    def test_no_entry_condition_takes_the_type_default_and_warns(
        self, assembler, errors, type, default
    ):
        assembler.execute([simple(), simple(type)])
        assert assembler.timelines[1].entryCondition == default
        assert (
            f"Timeline 2 ({type}) has no entry condition; '{default}' used"
            in messages(errors)
        )

    def test_blank_entry_condition_is_no_entry_condition(self, assembler, errors):
        assembler.execute([simple(), simple("early_termination", entry_condition=" ")])
        assert assembler.timelines[1].entryCondition == "Early termination"
        assert any("no entry condition" in m for m in messages(errors))

    @pytest.mark.parametrize(
        "type", ["main", "arm", "cohort", "profile", "unclassified"]
    )
    def test_other_families_keep_the_fixed_text_and_do_not_warn(
        self, assembler, errors, type
    ):
        assembler.execute([simple(type)])
        assert assembler.timelines[0].entryCondition == "Paricipant identified"
        assert not any("no entry condition" in m for m in messages(errors))

    def test_conditional_timeline_is_a_sibling_not_main(self, assembler):
        assembler.execute([simple(), simple("early_termination")])
        main, et = assembler.timelines
        assert (main.mainTimeline, et.mainTimeline) == (True, False)
        assert et.entryId == et.instances[0].id
        assert et.exits and et.instances[-1].timelineExitId == et.exits[0].id

    def test_a_copied_column_gets_its_own_encounter_for_now(self, assembler):
        """U4-5 interim (2026-09-26): column ids are scoped to one timeline,
        so a visit printed in two timelines is two Encounters until a copy
        reference exists (`protocol_corpus` register N78). Pinned so the change is seen when it lands."""
        main = timeline(
            [
                column("c1", "Treatment", "V1", "Day 1"),
                column("c2", "Treatment", "ED", "Day 1"),
            ]
        )
        et = timeline(
            [column("c2", "Treatment", "ED", "Day 1")], type="early_termination"
        )
        assembler.execute([main, et])
        assert [(e.name, e.label) for e in assembler.encounters] == [
            ("T1-E1", "V1"),
            ("T1-E2", "ED"),
            ("T2-E1", "ED"),
        ]
        ed_main = assembler.timelines[0].instances[1].encounterId
        ed_et = assembler.timelines[1].instances[0].encounterId
        assert ed_main != ed_et


class TestSkippedTimelines:
    def _empty(self, type="unclassified"):
        return timeline([], [activity("Orphan")], type=type)

    def test_a_timeline_with_no_columns_is_not_built(self, assembler, errors):
        assembler.execute([simple(), self._empty()])
        assert [t.name for t in assembler.timelines] == ["TIMELINE-1"]
        assert any(
            "Timeline 2 has no columns" in m and "1 activities" in m
            for m in messages(errors)
        )

    def test_it_leaves_no_orphan_activities(self, assembler):
        assembler.execute([simple(), self._empty()])
        assert "Orphan" not in [a.label for a in assembler.activities]

    def test_ordinals_keep_their_position_so_a_skip_leaves_a_gap(self, assembler):
        assembler.execute([simple(), self._empty(), simple("profile")])
        assert [t.name for t in assembler.timelines] == ["TIMELINE-1", "TIMELINE-3"]

    def test_the_main_flag_moves_to_a_built_timeline(self, assembler):
        assembler.execute([self._empty("main"), simple("unclassified")])
        assert [t.mainTimeline for t in assembler.timelines] == [True]

    def test_nothing_buildable_builds_nothing(self, assembler):
        assembler.execute([self._empty(), self._empty()])
        assert assembler.timelines == []

    def test_a_bad_pattern_does_not_stop_the_timeline(self, assembler, errors):
        """U4-17: always build the timeline if at all possible."""
        bad = timeline([column("c1", timing=value("D1", "D1"))])
        assembler.execute([bad, simple("profile")])
        assert [t.name for t in assembler.timelines] == ["TIMELINE-1", "TIMELINE-2"]
        assert assembler.timelines[0].timings[0].valueLabel == "D1"
        assert any(
            m.startswith("Timeline 1, column 'c1', timing:") and "'D1'" in m
            for m in messages(errors)
        )


class TestExtensions:
    def _urls(self, tl):
        return {e.url: e.valueString for e in tl.extensionAttributes}

    def test_nothing_classified_nothing_emitted(self, assembler):
        assembler.execute([simple()])
        assert assembler.timelines[0].extensionAttributes == []

    def test_a_profile_carries_the_family_and_its_classification(self, assembler):
        assembler.execute(
            [
                simple(),
                simple(
                    "profile",
                    classification={
                        "orientation": "transposed",
                        "unit": "hour",
                        "placement": "away",
                    },
                ),
            ]
        )
        assert self._urls(assembler.timelines[1]) == {
            TLF_EXT_URL: "profile",
            TLO_EXT_URL: "transposed",
            TLU_EXT_URL: "hour",
            TLP_EXT_URL: "away",
        }

    def test_an_absent_value_is_left_out(self, assembler):
        assembler.execute([simple("profile", classification={"unit": "minute"})])
        assert self._urls(assembler.timelines[0]) == {
            TLF_EXT_URL: "profile",
            TLU_EXT_URL: "minute",
        }

    def test_the_family_marks_profiles_only(self, assembler):
        """TLF's presence is what marks a profile to downstream readers."""
        assembler.execute([simple("arm", classification={"orientation": "upright"})])
        assert self._urls(assembler.timelines[0]) == {TLO_EXT_URL: "upright"}

    def test_findable_by_url(self, assembler):
        assembler.execute([simple("profile")])
        assert assembler.timelines[0].get_extension(TLF_EXT_URL).valueString == (
            "profile"
        )


# ----------------------------------------------------------------------
# Epochs, encounters, instances


class TestEpochs:
    def test_one_per_distinct_period(self, assembler):
        tl = timeline(
            [
                column("c1", "Screening"),
                column("c2", "Treatment"),
                column("c3", "treatment "),
                column("c4", "Follow-up"),
            ]
        )
        assembler.execute([tl])
        assert [e.name for e in assembler.epochs] == ["SCR", "TREAT", "FU"]
        instances = assembler.timelines[0].instances
        assert instances[1].epochId == instances[2].epochId

    def test_colliding_house_names_both_created(self, assembler):
        tl = timeline(
            [
                column("c1", "Period I - Screening"),
                column("c2", "Period II - Screening"),
            ]
        )
        assembler.execute([tl])
        assert [e.name for e in assembler.epochs] == ["SCR", "SCR2"]
        assert [e.label for e in assembler.epochs] == [
            "Period I - Screening",
            "Period II - Screening",
        ]

    def test_a_column_with_no_epoch_gets_an_empty_labelled_epoch(self, assembler):
        """Today's behaviour, kept until decision U4-6 is taken."""
        assembler.execute([timeline([column("c1"), column("c2")])])
        assert [(e.name, e.label) for e in assembler.epochs] == [("EP1", "")]

    def test_epochs_are_per_timeline(self, assembler):
        assembler.execute([simple(), simple("profile")])
        assert [e.name for e in assembler.epochs] == [
            "T1-SCR",
            "T1-TREAT",
            "T2-SCR",
            "T2-TREAT",
        ]


class TestEncounters:
    def test_one_per_column_never_merged(self, assembler):
        tl = timeline([column("c1", visit="D1"), column("c2", visit="D1")])
        assembler.execute([tl])
        assert [(e.name, e.label) for e in assembler.encounters] == [
            ("E1", "D1"),
            ("E2", "D1"),
        ]
        instances = assembler.timelines[0].instances
        assert [i.encounterId for i in instances] == [
            e.id for e in assembler.encounters
        ]

    def test_no_visit_is_an_empty_label(self, assembler):
        assembler.execute([timeline([column("c1")])])
        assert assembler.encounters[0].label == ""

    def test_namespaced_per_timeline(self, assembler):
        assembler.execute([simple(), simple("profile")])
        assert [e.name for e in assembler.encounters] == [
            "T1-E1",
            "T1-E2",
            "T2-E1",
            "T2-E2",
        ]


class TestInstances:
    def test_names_and_labels_from_the_timing_text(self, assembler):
        tl = timeline(
            [
                column("c1", timing="Day -1"),
                column("c2", timing="Day 1"),
                column("c3", timing="Week 12"),
                column("c4", timing={"text": "Cycle 2 Day 1", "pattern": None}),
                column("c5", visit="Final Visit/ET"),
            ]
        )
        assembler.execute([tl])
        instances = assembler.timelines[0].instances
        assert [i.name for i in instances] == [
            "D-1",
            "D1",
            "W12",
            "C2D1",
            "FINAL VISIT ET",
        ]
        assert [i.label for i in instances] == [
            "Day -1",
            "Day 1",
            "Week 12",
            "Cycle 2 Day 1",
            "",
        ]


# ----------------------------------------------------------------------
# Timings


class TestTimings:
    def test_relative_to_one_anchor(self, assembler):
        tl = timeline(
            [
                column("c1", timing="Day -7"),
                column("c2", timing="Day 1"),
                column("c3", timing="Day 8"),
            ]
        )
        assembler.execute([tl])
        (t,) = assembler.timelines
        assert timing_types(t) == ["Before", "Fixed Reference", "After"]
        assert [x.value for x in t.timings] == ["P7D", "PT0M", "P7D"]
        anchor = t.instances[1].id
        assert all(x.relativeToScheduledInstanceId == anchor for x in t.timings)
        assert [x.relativeFromScheduledInstanceId for x in t.timings] == [
            i.id for i in t.instances
        ]
        assert [x.name for x in t.timings] == ["TIM1", "TIM2", "TIM3"]
        assert t.timings[0].relativeToFrom.decode == "Start to Start"

    def test_value_labels_are_the_printed_text(self, assembler):
        tl = timeline([column("c1", timing=value("D 1", "Day 1"))])
        assembler.execute([tl])
        timing = assembler.timelines[0].timings[0]
        assert (timing.valueLabel, timing.label) == ("D 1", "D 1")

    def test_mixed_units_use_the_absolute_value(self, assembler, errors):
        tl = timeline([column("c1", timing="Day 1"), column("c2", timing="Week 2")])
        assembler.execute([tl])
        assert assembler.timelines[0].timings[1].value == "P2W"
        assert any("differs from anchor unit" in m for m in messages(errors))

    def test_an_unreadable_timing_is_zero_after_the_previous_column(self, assembler):
        """U4-3. A cycle and day printed together in the timing field, with no
        cycle field, stay unread: splitting them is stage 1's (U4-26)."""
        tl = timeline(
            [
                column("c1", timing="Day 1"),
                column("c2", timing="Day 8"),
                column("c3", timing={"text": "Cycle 2 Day 1", "pattern": None}),
            ]
        )
        assembler.execute([tl])
        (t,) = assembler.timelines
        assert t.timings[2].value == "PT0M"
        assert timing_types(t)[2] == "After"
        assert t.timings[2].relativeToScheduledInstanceId == t.instances[1].id
        assert t.timings[2].valueLabel == "Cycle 2 Day 1"

    def test_single_cycles_are_timed_and_named(self, assembler, errors):
        """Issue 66: C2D1 from the anchor, C2D8 from C2D1, names from the
        parsed cycle and day, printed text kept as the labels."""
        cycle = {
            1: {"cycle": value("Cycle 1"), "cycle_length": value("21 days")},
            2: {"cycle": value("C2", "Cycle 2"), "cycle_length": value("21 days")},
        }
        tl = timeline(
            [
                column("c1", timing="Day 1", **cycle[1]),
                column("c2", timing=value("D8", "Day 8"), **cycle[1]),
                column("c3", timing="Day 1", **cycle[2]),
                column("c4", timing=value("D8", "Day 8"), **cycle[2]),
            ]
        )
        assembler.execute([tl])
        (t,) = assembler.timelines
        assert [i.name for i in t.instances] == ["C1D1", "C1D8", "C2D1", "C2D8"]
        assert [x.value for x in t.timings] == ["PT0M", "P7D", "P21D", "P7D"]
        assert timing_types(t) == ["Fixed Reference", "After", "After", "After"]
        assert t.timings[3].relativeToScheduledInstanceId == t.instances[2].id
        assert t.timings[3].valueLabel == "D8"
        assert not any("cycle" in m for m in messages(errors))

    def test_a_cycle_with_no_day_one_gets_a_start_marker(self, assembler, errors):
        """Issue 67: C2 prints no Day 1, so a C2D1 instance marks its start —
        no encounter, no activities, the cycle's epoch — timed from C1D1 by
        cycle 1's length; C3D1 from C2D1 by cycle 2's length."""
        cycle = {
            n: {"cycle": value(f"Cycle {n}"), "cycle_length": value(length)}
            for n, length in ((1, "21 days"), (2, "28 days"), (3, "28 days"))
        }
        tl = timeline(
            [
                column("c1", epoch="Treatment", timing="Day 1", **cycle[1]),
                column("c2", epoch="Treatment", timing="Day 8", **cycle[1]),
                column("c3", epoch="Treatment 2", timing="Day 8", **cycle[2]),
                column("c4", epoch="Treatment 2", timing="Day 15", **cycle[2]),
                column("c5", epoch="Treatment 2", timing="Day 1", **cycle[3]),
            ],
            activities=[activity("Vitals", ["c1", "c3"])],
        )
        assembler.execute([tl])
        (t,) = assembler.timelines
        names = [i.name for i in t.instances]
        assert names == ["C1D1", "C1D8", "C2D1", "C2D8", "C2D15", "C3D1"]
        marker = t.instances[2]
        assert marker.encounterId is None
        assert marker.activityIds == []
        assert marker.epochId == t.instances[3].epochId != t.instances[0].epochId
        assert t.instances[1].defaultConditionId == marker.id
        assert marker.defaultConditionId == t.instances[3].id
        assert len(assembler.encounters) == 5
        assert len(t.timings) == len(t.instances) == 6
        by_id = {i.id: i.name for i in t.instances}
        links = [
            (
                by_id[x.relativeFromScheduledInstanceId],
                x.value,
                by_id[x.relativeToScheduledInstanceId],
            )
            for x in t.timings
        ]
        assert links == [
            ("C1D1", "PT0M", "C1D1"),
            ("C1D8", "P7D", "C1D1"),
            ("C2D1", "P21D", "C1D1"),
            ("C2D8", "P7D", "C2D1"),
            ("C2D15", "P14D", "C2D1"),
            ("C3D1", "P28D", "C2D1"),
        ]
        assert (t.timings[2].valueLabel, t.timings[2].label) == ("", "")

    def test_every_instance_is_timed(self, assembler, errors):
        """A blank timing used to get no Timing at all (design § 2)."""
        tl = timeline([column("c1", visit="V1"), column("c2", timing="Day 7")])
        assembler.execute([tl])
        (t,) = assembler.timelines
        assert len(t.timings) == len(t.instances) == 2
        assert [(x.valueLabel, x.label) for x in t.timings] == [
            ("", ""),
            ("Day 7", "Day 7"),
        ]
        assert timing_types(t) == ["Before", "Fixed Reference"]
        assert any("column 'c1': no readable timing" in m for m in messages(errors))

    def test_text_only_timing_is_read(self, assembler):
        tl = timeline(
            [
                column("c1", timing={"text": "-7", "pattern": None}),
                column("c2", timing={"text": "1", "pattern": None}),
                column("c3", timing={"text": "15", "pattern": None}),
            ],
            rows={"timing": "Days from randomization"},
        )
        assembler.execute([tl])
        (t,) = assembler.timelines
        assert [x.value for x in t.timings] == ["P7D", "PT0M", "P14D"]
        assert [x.valueLabel for x in t.timings] == ["-7", "1", "15"]

    def test_a_time_range_is_labelled_decoded(self, assembler):
        """U4-21: decoded start and window as labels, printed text as label."""
        tl = timeline(
            [
                column("c1", timing=value("≤28", "Day -28 to Day -1")),
                column("c2", timing="Day 1"),
            ]
        )
        assembler.execute([tl])
        timing = assembler.timelines[0].timings[0]
        assert (timing.value, timing.valueLabel, timing.label) == (
            "P28D",
            "Day -28",
            "≤28",
        )
        assert (timing.windowLabel, timing.windowLower, timing.windowUpper) == (
            "-0..+27 days",
            "",
            "P27D",
        )

    def test_printed_up_to_before_the_anchor(self, assembler):
        tl = timeline(
            [
                column("c1", timing={"text": "≤42", "pattern": None}),
                column("c2", timing={"text": "1", "pattern": None}),
            ],
            rows={"timing": "Days from randomization"},
        )
        assembler.execute([tl])
        timing = assembler.timelines[0].timings[0]
        assert (timing.value, timing.valueLabel, timing.label) == (
            "P42D",
            "Day -42",
            "≤42",
        )
        assert timing.windowUpper == "P41D"

    def test_a_window_in_the_timing_cell(self, assembler):
        tl = timeline(
            [
                column("c1", timing="Day 1"),
                column("c2", timing={"text": "Day 15 ± 3", "pattern": None}),
            ]
        )
        assembler.execute([tl])
        timing = assembler.timelines[0].timings[1]
        assert (timing.valueLabel, timing.windowLabel) == ("Day 15 ± 3", "-3..+3 days")
        assert (timing.windowLower, timing.windowUpper) == ("P3D", "P3D")

    def test_the_expander_follows_a_zero_timing_chain(self, assembler):
        tl = timeline(
            [
                column("c1", timing={"text": "Screening", "pattern": None}),
                column("c2", timing="Day -3"),
                column("c3", timing="Day 1"),
                column("c4", timing="Day 8"),
                column("c5", timing={"text": "ET", "pattern": None}),
            ]
        )
        assembler.execute([tl])
        (t,) = assembler.timelines
        ticks = [
            Timepoint(None, t, sai, Errors(), 1, 0).tick // 86400 for sai in t.instances
        ]
        assert ticks == [-3, -3, 0, 7, 7]

    def test_hours(self, assembler):
        tl = timeline([column("c1", timing="Hour 0"), column("c2", timing="Hour 4")])
        assembler.execute([tl])
        assert [x.value for x in assembler.timelines[0].timings] == ["PT0M", "PT4H"]


class TestWindows:
    def _timing(self, assembler, window):
        assembler.execute([timeline([column("c1", timing="Day 1", window=window)])])
        return assembler.timelines[0].timings[0]

    def test_a_window(self, assembler):
        timing = self._timing(assembler, value("(±3 days)", "-3..+3 days"))
        assert timing.windowLabel == "(±3 days)"
        assert (timing.windowLower, timing.windowUpper) == ("P3D", "P3D")

    def test_an_asymmetric_window(self, assembler):
        timing = self._timing(assembler, value("-0..+2 hours"))
        assert (timing.windowLower, timing.windowUpper) == ("", "PT2H")

    def test_a_zero_window_has_an_empty_label(self, assembler):
        timing = self._timing(assembler, value("", "-0..+0 days"))
        assert (timing.windowLabel, timing.windowLower, timing.windowUpper) == (
            "",
            "",
            "",
        )

    def test_no_window(self, assembler):
        timing = self._timing(assembler, None)
        assert (timing.windowLabel, timing.windowLower, timing.windowUpper) == (
            None,
            "",
            "",
        )

    def test_a_text_only_window(self, assembler):
        timing = self._timing(assembler, {"text": "±2", "pattern": None})
        assert (timing.windowLabel, timing.windowLower, timing.windowUpper) == (
            "±2",
            "P2D",
            "P2D",
        )

    def test_an_unread_window_keeps_its_printed_label(self, assembler):
        timing = self._timing(assembler, {"text": "See Section 1.3", "pattern": None})
        assert (timing.windowLabel, timing.windowLower, timing.windowUpper) == (
            "See Section 1.3",
            "",
            "",
        )


# ----------------------------------------------------------------------
# Activities and cells


class TestActivities:
    def test_cells_link_activities_to_instances(self, assembler):
        tl = timeline(
            [column("c1"), column("c2")],
            [activity("Consent", ["c1"]), activity("Vitals", ["c1", "c2"])],
        )
        assembler.execute([tl])
        consent, vitals = assembler.activities
        first, second = assembler.timelines[0].instances
        assert first.activityIds == [consent.id, vitals.id]
        assert second.activityIds == [vitals.id]

    def test_parents_and_children(self, assembler):
        tl = timeline(
            [column("c1")],
            [
                activity("Laboratory"),
                activity("Haematology", ["c1"], parent="Laboratory"),
                activity("Chemistry", ["c1"], parent="Laboratory"),
            ],
        )
        assembler.execute([tl])
        lab, haem, chem = assembler.activities
        assert lab.childIds == [haem.id, chem.id]
        assert assembler.timelines[0].instances[0].activityIds == [haem.id, chem.id]

    def test_a_child_listed_before_its_parent_is_still_linked(self, assembler):
        tl = timeline(
            [column("c1")],
            [activity("Haematology", parent="Laboratory"), activity("Laboratory")],
        )
        assembler.execute([tl])
        haem, lab = assembler.activities
        assert lab.childIds == [haem.id]

    def test_shared_across_timelines(self, assembler):
        second = timeline(
            [column("c1", timing="Hour 0")],
            [activity("Blood Draw", ["c1"]), activity("PK Sample", ["c1"])],
            type="profile",
        )
        assembler.execute([simple(), second])
        assert [a.label for a in assembler.activities] == [
            "Consent",
            "Blood Draw",
            "PK Sample",
        ]
        blood = assembler.activities[1]
        assert blood.id in assembler.timelines[0].instances[1].activityIds
        assert blood.id in assembler.timelines[1].instances[0].activityIds

    def test_identity_is_space_and_case(self, assembler):
        tl = timeline(
            [column("c1"), column("c2")],
            [activity("Vital signs", ["c1"]), activity("vital signs ", ["c2"])],
        )
        assembler.execute([tl])
        assert len(assembler.activities) == 1

    def test_activities_are_ordered_across_timelines(self, assembler):
        assembler.execute([simple()])
        consent, blood = assembler.activities
        assert (consent.previousId, consent.nextId) == (None, blood.id)
        assert (blood.previousId, blood.nextId) == (consent.id, None)


class TestBiomedicalConcepts:
    def _run(self, assembler, bcs):
        assembler.execute([timeline([column("c1")], [activity("Vitals", bcs=bcs)])])
        return assembler.activities[0]

    def test_library_and_surrogate(self, assembler):
        vitals = self._run(assembler, ["Sex", "Unlisted Local Measurement"])
        assert [b.name for b in assembler.biomedical_concepts] == ["Sex"]
        assert [s.name for s in assembler.biomedical_concept_surrogates] == [
            "Unlisted Local Measurement"
        ]
        assert vitals.biomedicalConceptIds == [assembler.biomedical_concepts[0].id]
        assert vitals.bcSurrogateIds == [assembler.biomedical_concept_surrogates[0].id]
        assert [p.name for p in vitals.definedProcedures] == [
            "Sex",
            "Unlisted Local Measurement",
        ]

    def test_a_procedure_still_carries_the_placeholder_code(self, assembler):
        """Design § 8 — out of scope for issue 63, pinned until fixed."""
        vitals = self._run(assembler, ["Unlisted Local Measurement"])
        assert vitals.definedProcedures[0].code.code == "12345"

    def test_a_library_bc_that_fails_is_warned(self, assembler, errors, monkeypatch):
        monkeypatch.setattr(
            assembler._builder.cdisc_bc_library, "exists", lambda name: True
        )
        monkeypatch.setattr(assembler._builder, "bc", lambda name: None)
        vitals = self._run(assembler, ["Blood Pressure"])
        assert vitals.biomedicalConceptIds == []
        assert any("Failed to create BC" in m for m in messages(errors))

    def test_a_library_bc_is_used(self, assembler, monkeypatch):
        fake = types.SimpleNamespace(id="BC-X")
        monkeypatch.setattr(
            assembler._builder.cdisc_bc_library, "exists", lambda name: True
        )
        monkeypatch.setattr(assembler._builder, "bc", lambda name: fake)
        vitals = self._run(assembler, ["Blood Pressure"])
        assert vitals.biomedicalConceptIds == ["BC-X"]

    @pytest.mark.parametrize(
        "klass, message",
        [
            ("BiomedicalConceptSurrogate", "Failed to create surrogate BC"),
            ("Procedure", "Failed to create procedure"),
        ],
    )
    def test_a_create_that_fails_is_warned(
        self, assembler, errors, monkeypatch, klass, message
    ):
        real_create = assembler._builder.create

        def create(k, params, *args, **kwargs):
            if k.__name__ == klass:
                return None
            return real_create(k, params, *args, **kwargs)

        monkeypatch.setattr(assembler._builder, "create", create)
        self._run(assembler, ["MadeUpBC"])
        assert any(message in m for m in messages(errors))


# ----------------------------------------------------------------------
# Footnotes → conditions


class TestConditions:
    def _run(self, assembler, footnotes, **kwargs):
        tl = timeline(
            [column("c1", visit="V1", markers=kwargs.get("visit", [])), column("c2")],
            [
                activity(
                    "Consent",
                    [{"column": "c2", "text": "X", "markers": kwargs.get("cell", [])}],
                    markers=kwargs.get("activity", []),
                )
            ],
            footnotes,
        )
        assembler.execute([tl])
        return assembler.conditions

    def test_a_visit_marker_is_context_only(self, assembler):
        (c,) = self._run(assembler, [{"marker": "a", "text": "Note."}], visit=["a"])
        assert c.contextIds == [assembler.timelines[0].instances[0].id]
        assert c.appliesToIds == []
        assert (c.name, c.label, c.text) == ("COND1", "a", "Note.")

    def test_an_activity_marker(self, assembler):
        (c,) = self._run(assembler, [{"marker": "b", "text": "B."}], activity=["b"])
        assert c.contextIds == [assembler.activities[0].id]
        assert c.appliesToIds == []

    def test_a_cell_marker_is_context_and_applies_to(self, assembler):
        (c,) = self._run(assembler, [{"marker": "c", "text": "C."}], cell=["c"])
        assert c.contextIds == [assembler.timelines[0].instances[1].id]
        assert c.appliesToIds == [assembler.activities[0].id]

    def test_one_marker_in_several_places(self, assembler):
        (c,) = self._run(
            assembler, [{"marker": "a", "text": "A."}], visit=["a"], cell=["a"]
        )
        instances = assembler.timelines[0].instances
        assert c.contextIds == [instances[0].id, instances[1].id]
        assert c.appliesToIds == [assembler.activities[0].id]

    def test_unanchored_and_unmarked_footnotes_are_dropped_and_counted(
        self, assembler, errors
    ):
        conditions = self._run(
            assembler,
            [
                {"marker": "a", "text": "Kept."},
                {"marker": "z", "text": "Nowhere."},
                {"marker": "", "text": "No marker."},
            ],
            visit=["a"],
        )
        assert [c.name for c in conditions] == ["COND1"]
        found = messages(errors)
        assert any("Failed to align condition" in m for m in found)
        assert any("Condition has no reference" in m for m in found)
        assert any(
            "Conditions T1: in=3, referenced=2, aligned=1, dropped_no_ref=1, "
            "dropped_no_match=1" in m
            for m in found
        )

    def test_a_summary_even_with_no_footnotes(self, assembler, errors):
        self._run(assembler, [])
        assert any("Conditions T1: in=0" in m for m in messages(errors))

    def test_markers_are_scoped_to_one_timeline(self, assembler):
        second = timeline(
            [column("c1")], [activity("PK")], [{"marker": "a", "text": "Other."}]
        )
        first = timeline(
            [column("c1", visit="V1", markers=["a"])],
            [],
            [{"marker": "a", "text": "Mine."}],
        )
        assembler.execute([first, second])
        assert [c.text for c in assembler.conditions] == ["Mine."]

    # Issue 64: markers are carried per header value.

    @pytest.mark.parametrize("field", ["epoch", "timing", "window"])
    def test_a_marker_on_any_header_value_is_context(self, assembler, field):
        texts = {"epoch": "Screening", "timing": "Day 1", "window": "-1..+1 days"}
        tl = timeline(
            [
                column("c1", **{field: value(texts[field], markers=["m"])}),
                column("c2", visit="V2"),
            ],
            [activity("Consent", ["c2"])],
            [{"marker": "m", "text": "M."}],
        )
        assembler.execute([tl])
        (c,) = assembler.conditions
        assert c.contextIds == [assembler.timelines[0].instances[0].id]
        assert c.appliesToIds == []

    def test_one_marker_on_two_values_of_a_column_links_once(self, assembler):
        tl = timeline(
            [
                column(
                    "c1",
                    visit=value("V1", markers=["a"]),
                    timing=value("Day 1", markers=["a"]),
                )
            ],
            [],
            [{"marker": "a", "text": "A."}],
        )
        assembler.execute([tl])
        (c,) = assembler.conditions
        assert c.contextIds == [assembler.timelines[0].instances[0].id]


# ----------------------------------------------------------------------
# Redaction (issue 64)


def _cci() -> dict:
    return {"text": "CCI", "pattern": "CCI"}


class TestRedaction:
    def test_a_redacted_timing_builds(self, assembler, errors):
        tl = timeline(
            [
                column("c1", "Screening", "Visit 1", _cci()),
                column("c2", "Treatment", "Visit 2", _cci()),
                column("c3", "Treatment", "Visit 3", _cci()),
            ],
            [activity("Consent", ["c1"]), activity("Dosing", ["c2", "c3"])],
        )
        assembler.execute([tl])
        (built,) = assembler.timelines
        assert len(built.instances) == 3
        assert len(built.timings) == 3
        assert not any("not created" in m for m in messages(errors))
        # The printed text is carried as the label; no number is guessed.
        assert [t.label for t in built.timings] == ["CCI", "CCI", "CCI"]
        assert {t.value for t in built.timings} == {"PT0M"}

    def test_a_redacted_timing_does_not_name_the_instance(self, assembler):
        tl = timeline(
            [
                column("c1", visit="Visit 1", timing=_cci()),
                column("c2", visit="Visit 2", timing=_cci()),
            ],
        )
        assembler.execute([tl])
        names = [i.name for i in assembler.timelines[0].instances]
        assert names == ["VISIT 1", "VISIT 2"]

    def test_redacted_timing_and_visit_fall_back_to_position(self, assembler):
        tl = timeline(
            [
                column("c1", visit=_cci(), timing=_cci()),
                column("c2", visit=_cci(), timing=_cci()),
            ],
        )
        assembler.execute([tl])
        names = [i.name for i in assembler.timelines[0].instances]
        assert names == ["T1-SAI-1", "T1-SAI-2"]

    def test_a_redacted_window_makes_no_window(self, assembler):
        tl = timeline([column("c1", visit="V1", timing="Day 1", window=_cci())])
        assembler.execute([tl])
        (timing,) = assembler.timelines[0].timings
        assert (timing.windowLower, timing.windowUpper) == ("", "")
        assert timing.windowLabel == "CCI"

    def test_a_consecutive_redacted_run_is_one_epoch(self, assembler):
        tl = timeline(
            [
                column("c1", _cci(), "V1"),
                column("c2", _cci(), "V2"),
                column("c3", "Follow-up", "V3"),
            ],
        )
        assembler.execute([tl])
        assert [e.label for e in assembler.epochs] == ["CCI", "Follow-up"]
        instances = assembler.timelines[0].instances
        assert instances[0].epochId == instances[1].epochId

    def test_separate_redacted_runs_are_separate_epochs(self, assembler):
        tl = timeline(
            [
                column("c1", _cci(), "V1"),
                column("c2", "Treatment", "V2"),
                column("c3", _cci(), "V3"),
                column("c4", _cci(), "V4"),
            ],
        )
        assembler.execute([tl])
        epochs = assembler.epochs
        assert [e.label for e in epochs] == ["CCI", "Treatment", "CCI"]
        assert epochs[0].name != epochs[2].name
        instances = assembler.timelines[0].instances
        assert instances[0].epochId != instances[2].epochId
        assert instances[2].epochId == instances[3].epochId

    def test_printed_cci_with_no_pattern_is_ordinary_text(self, assembler):
        # Only the pattern states a redaction: text-only `CCI` epochs group by
        # their text as before.
        text_only = {"text": "CCI", "pattern": None}
        tl = timeline(
            [
                column("c1", text_only, "V1"),
                column("c2", "Treatment", "V2"),
                column("c3", text_only, "V3"),
            ],
        )
        assembler.execute([tl])
        assert [e.label for e in assembler.epochs] == ["CCI", "Treatment"]
