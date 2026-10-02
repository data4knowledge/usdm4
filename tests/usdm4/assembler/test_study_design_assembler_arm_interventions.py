"""Tests for arm → intervention wiring (ArmInput.intervention_names).

USDM has no direct arm → intervention reference: the linkage is encoded as
cell → element → studyInterventionIds. Covers:

- Synthesised per-arm element attached to the arm's cells (no explicit
  elements in the input — the extraction path)
- No timeline epochs: one synthesised Treatment Epoch (extension 017) so
  the element lands on a cell; not synthesised without resolvable arm
  interventions or with explicit cells / elements
- Explicit elements are authoritative: reachability check warns, never
  mutates
- Unknown intervention references warn and are skipped
- Exception / None-return handling in element synthesis
"""

import os
import pathlib
from unittest.mock import patch

import pytest
from simple_error_log.errors import Errors

from usdm4.api.extensions_d4k import EPP_EXT_URL
from usdm4.api.study_epoch import StudyEpoch
from usdm4.assembler.population_assembler import PopulationAssembler
from usdm4.assembler.study_design_assembler import StudyDesignAssembler
from usdm4.assembler.timeline_assembler import TimelineAssembler
from usdm4.builder.builder import Builder


def _root_path():
    base = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


@pytest.fixture(scope="module")
def builder():
    # Module-scoped: first CT lookup on a fresh Builder is expensive.
    return Builder(_root_path(), Errors())


@pytest.fixture
def errors():
    return Errors()


@pytest.fixture
def population_assembler(builder, errors):
    builder.clear()  # Root of the per-test fixture chain — reset cross-refs.
    pa = PopulationAssembler(builder, errors)
    pa.execute(
        {"label": "Pop", "inclusion_exclusion": {"inclusion": [], "exclusion": []}}
    )
    return pa


@pytest.fixture
def timeline_with_epoch(builder, errors, population_assembler):
    # Depends on population_assembler so builder.clear() has already run.
    ta = TimelineAssembler(builder, errors)
    ta.clear()
    epoch = builder.create(
        StudyEpoch,
        {
            "name": "EPOCH-TREATMENT",
            "label": "Treatment",
            "description": "Treatment epoch",
            "type": builder.klass_and_attribute_value(
                StudyEpoch, "type", "Treatment Epoch"
            ),
        },
    )
    ta._epochs = [epoch]
    return ta


@pytest.fixture
def timeline_empty(builder, errors, population_assembler):
    ta = TimelineAssembler(builder, errors)
    ta.clear()
    return ta


@pytest.fixture
def assembler(builder, errors):
    return StudyDesignAssembler(builder, errors)


def _base_data(**overrides) -> dict:
    data = {
        "label": "Design",
        "rationale": "Rationale",
        "trial_phase": "1",
        "interventions": [{"name": "Drug A"}, {"name": "Placebo"}],
        "arms": [
            {
                "name": "Active Arm",
                "type": "Experimental",
                "intervention_names": ["Drug A"],
            },
            {"name": "Placebo Arm", "type": "Placebo Comparator"},
        ],
    }
    data.update(overrides)
    return data


class TestArmInterventionWiring:
    def test_synthesised_element_attached_to_arm_cells(
        self, assembler, population_assembler, timeline_with_epoch
    ):
        assembler.execute(_base_data(), population_assembler, timeline_with_epoch)
        design = assembler.study_design
        drug_a = assembler.study_interventions[0]

        elements = [e for e in design.elements if e.name == "EL-ACTIVE-ARM"]
        assert len(elements) == 1
        element = elements[0]
        assert element.studyInterventionIds == [drug_a.id]
        assert element.label == "Active Arm interventions"

        active_arm = design.arms[0]
        active_cells = [c for c in design.studyCells if c.armId == active_arm.id]
        assert active_cells
        assert all(element.id in c.elementIds for c in active_cells)

        # The placebo arm (no intervention_names) is untouched.
        placebo_arm = design.arms[1]
        placebo_cells = [c for c in design.studyCells if c.armId == placebo_arm.id]
        assert all(c.elementIds == [] for c in placebo_cells)

    def test_no_epochs_element_placed_on_synthesised_epoch_cell(
        self, assembler, population_assembler, timeline_empty
    ):
        # No timeline epochs → one synthesised Treatment Epoch, one cell per
        # arm, and the arm's element on its cell.
        assembler.execute(_base_data(), population_assembler, timeline_empty)
        design = assembler.study_design
        assert len(design.epochs) == 1
        assert len(design.studyCells) == len(design.arms) == 2
        elements = [e for e in design.elements if e.name == "EL-ACTIVE-ARM"]
        assert len(elements) == 1
        assert elements[0].studyInterventionIds == [assembler.study_interventions[0].id]
        active_cell = next(c for c in design.studyCells if c.armId == design.arms[0].id)
        assert active_cell.elementIds == [elements[0].id]

    def test_multiple_interventions_on_one_arm(
        self, assembler, population_assembler, timeline_with_epoch
    ):
        data = _base_data()
        data["arms"][0]["intervention_names"] = ["Drug A", "Placebo"]
        assembler.execute(data, population_assembler, timeline_with_epoch)
        element = [
            e for e in assembler.study_design.elements if e.name == "EL-ACTIVE-ARM"
        ][0]
        assert element.studyInterventionIds == [
            i.id for i in assembler.study_interventions
        ]

    def test_explicit_elements_consistent_no_warning_no_mutation(
        self, assembler, population_assembler, timeline_with_epoch, errors
    ):
        data = _base_data(
            elements=[{"name": "El1", "intervention_names": ["Drug A"]}],
            cells=[{"arm": "Active Arm", "epoch": "Treatment", "elements": ["El1"]}],
        )
        assembler.execute(data, population_assembler, timeline_with_epoch)
        design = assembler.study_design
        # No synthetic element added; explicit structure untouched.
        assert [e.name for e in design.elements] == ["EL1"]
        assert "not reachable" not in str(errors.to_dict(Errors.WARNING))

    def test_explicit_elements_inconsistent_warns_without_mutation(
        self, assembler, population_assembler, timeline_with_epoch, errors
    ):
        data = _base_data(
            elements=[{"name": "El1", "intervention_names": ["Placebo"]}],
            cells=[{"arm": "Active Arm", "epoch": "Treatment", "elements": ["El1"]}],
        )
        assembler.execute(data, population_assembler, timeline_with_epoch)
        design = assembler.study_design
        assert [e.name for e in design.elements] == ["EL1"]
        assert "not reachable" in str(errors.to_dict(Errors.WARNING))

    def test_unknown_intervention_reference_warns_and_skips(
        self, assembler, population_assembler, timeline_with_epoch
    ):
        data = _base_data()
        data["arms"][0]["intervention_names"] = ["Drug X"]
        assembler.execute(data, population_assembler, timeline_with_epoch)
        # All references unresolved → no synthetic element at all.
        assert [
            e for e in assembler.study_design.elements if e.name == "EL-ACTIVE-ARM"
        ] == []

    def test_arm_creation_failure_skips_wiring(
        self, assembler, population_assembler, timeline_with_epoch, builder
    ):
        original_create = builder.create

        def maybe_raise(cls, params):
            if cls.__name__ == "StudyArm":
                raise RuntimeError("forced")
            return original_create(cls, params)

        with patch.object(builder, "create", side_effect=maybe_raise):
            assembler.execute(_base_data(), population_assembler, timeline_with_epoch)
        # No arms → no wiring, and no crash.
        assert assembler.study_design.arms == []

    def test_element_synthesis_exception_logged(
        self, assembler, population_assembler, timeline_with_epoch, builder
    ):
        original_create = builder.create

        def maybe_raise(cls, params):
            if cls.__name__ == "StudyElement":
                raise RuntimeError("forced")
            return original_create(cls, params)

        with patch.object(builder, "create", side_effect=maybe_raise):
            assembler.execute(_base_data(), population_assembler, timeline_with_epoch)
        assert assembler.study_design.elements == []

    def test_element_synthesis_none_return_handled(
        self, assembler, population_assembler, timeline_with_epoch, builder
    ):
        original_create = builder.create

        def maybe_none(cls, params):
            if cls.__name__ == "StudyElement":
                return None
            return original_create(cls, params)

        with patch.object(builder, "create", side_effect=maybe_none):
            assembler.execute(_base_data(), population_assembler, timeline_with_epoch)
        design = assembler.study_design
        assert design.elements == []
        # Cells remain unmutated.
        assert all(c.elementIds == [] for c in design.studyCells)


class TestSynthesisedEpoch:
    """No timeline epochs + arms naming interventions → one Treatment Epoch
    marked with the epoch-provenance extension (EPP_EXT_URL)."""

    def test_epoch_shape_and_extension(
        self, assembler, population_assembler, timeline_empty
    ):
        assembler.execute(_base_data(), population_assembler, timeline_empty)
        epoch = assembler.study_design.epochs[0]
        assert epoch.name == "TREATMENT-EPOCH"
        assert epoch.label == "Treatment Epoch"
        assert epoch.type.code == "C101526"
        assert epoch.previousId is None and epoch.nextId is None
        ext = epoch.get_extension(EPP_EXT_URL)
        assert ext is not None
        assert ext.valueString == StudyDesignAssembler.EPOCH_SYNTHESISED

    def test_every_cell_uses_the_synthesised_epoch(
        self, assembler, population_assembler, timeline_empty
    ):
        assembler.execute(_base_data(), population_assembler, timeline_empty)
        design = assembler.study_design
        epoch_id = design.epochs[0].id
        assert all(c.epochId == epoch_id for c in design.studyCells)

    def test_timeline_epochs_used_unchanged(
        self, assembler, population_assembler, timeline_with_epoch
    ):
        assembler.execute(_base_data(), population_assembler, timeline_with_epoch)
        design = assembler.study_design
        assert [e.name for e in design.epochs] == ["EPOCH-TREATMENT"]
        assert design.epochs[0].get_extension(EPP_EXT_URL) is None

    def test_no_arms_no_epoch(self, assembler, population_assembler, timeline_empty):
        assembler.execute(
            _base_data(arms=[]), population_assembler, timeline_empty
        )
        assert assembler.study_design.epochs == []
        assert assembler.study_design.studyCells == []

    def test_arms_without_interventions_no_epoch(
        self, assembler, population_assembler, timeline_empty
    ):
        data = _base_data()
        data["arms"][0].pop("intervention_names")
        assembler.execute(data, population_assembler, timeline_empty)
        assert assembler.study_design.epochs == []
        assert assembler.study_design.studyCells == []

    def test_unresolved_interventions_no_epoch(
        self, assembler, population_assembler, timeline_empty
    ):
        data = _base_data()
        data["arms"][0]["intervention_names"] = ["Drug X"]
        assembler.execute(data, population_assembler, timeline_empty)
        assert assembler.study_design.epochs == []

    def test_explicit_elements_no_epoch(
        self, assembler, population_assembler, timeline_empty
    ):
        data = _base_data(
            elements=[{"name": "El1", "intervention_names": ["Drug A"]}]
        )
        assembler.execute(data, population_assembler, timeline_empty)
        assert assembler.study_design.epochs == []

    def test_epoch_synthesis_exception_logged(
        self, assembler, population_assembler, timeline_empty, builder, errors
    ):
        original_create = builder.create

        def maybe_raise(cls, params):
            if cls.__name__ == "StudyEpoch":
                raise RuntimeError("forced")
            return original_create(cls, params)

        with patch.object(builder, "create", side_effect=maybe_raise):
            assembler.execute(_base_data(), population_assembler, timeline_empty)
        design = assembler.study_design
        assert design.epochs == []
        assert design.studyCells == []
        assert "synthesis of the treatment epoch" in str(errors.to_dict())

    def test_epoch_synthesis_none_return_handled(
        self, assembler, population_assembler, timeline_empty, builder
    ):
        original_create = builder.create

        def maybe_none(cls, params):
            if cls.__name__ == "StudyEpoch":
                return None
            return original_create(cls, params)

        with patch.object(builder, "create", side_effect=maybe_none):
            assembler.execute(_base_data(), population_assembler, timeline_empty)
        assert assembler.study_design.epochs == []
