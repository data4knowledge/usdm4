"""Branch-coverage supplements for StudyDesignAssembler.

The wiring tests in test_study_design_assembler.py cover the happy
paths. These hit the lower-traffic warning branches:

- Element referencing an undeclared intervention
- Cell referencing an unknown arm / epoch / element
- Cohort with arm_names referencing an unknown arm
- execute() top-level exception handler
- _build_administrations with dose/route/frequency + exception paths
- _synthesise_cell_grid exception handler
- _wire_cohorts_to_arms — raw cohort without name / cohort obj not found
"""

import os
import pathlib
from unittest.mock import patch

import pytest
from simple_error_log.errors import Errors

# Mirror the primary test file's import pattern (usdm4.* for API classes;
# src.usdm4.* for the assemblers/builder we're exercising).
from usdm4.api.study_epoch import StudyEpoch
from src.usdm4.assembler.population_assembler import PopulationAssembler
from src.usdm4.assembler.study_design_assembler import StudyDesignAssembler
from src.usdm4.assembler.timeline_assembler import TimelineAssembler
from src.usdm4.builder.builder import Builder


def _root_path():
    base = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


@pytest.fixture
def builder():
    b = Builder(_root_path(), Errors())
    b.clear()
    return b


@pytest.fixture
def errors():
    return Errors()


@pytest.fixture
def population_assembler(builder, errors):
    pa = PopulationAssembler(builder, errors)
    pa.execute(
        {
            "label": "Pop",
            "inclusion_exclusion": {"inclusion": [], "exclusion": []},
        }
    )
    return pa


def _make_epoch(builder, label):
    return builder.create(
        StudyEpoch,
        {
            "name": f"EPOCH-{label.upper()}",
            "label": label,
            "description": f"Epoch {label}",
            "type": builder.klass_and_attribute_value(
                StudyEpoch, "type", "Treatment Epoch"
            ),
        },
    )


@pytest.fixture
def timeline_with_epochs(builder, errors):
    ta = TimelineAssembler(builder, errors)
    ta._epochs = [_make_epoch(builder, "Treatment")]
    ta._encounters = []
    ta._activities = []
    ta._timelines = []
    return ta


@pytest.fixture
def assembler(builder, errors):
    return StudyDesignAssembler(builder, errors)


# ---------------------------------------------------------------------------
# execute() top-level exception handler
# ---------------------------------------------------------------------------


def test_execute_missing_required_key_is_logged(
    assembler, population_assembler, timeline_with_epochs
):
    """Missing 'rationale' (referenced directly in execute) raises
    KeyError inside the builder.create call — caught and logged."""
    data = {"label": "Study", "trial_phase": "Phase II"}  # no rationale
    assembler.execute(data, population_assembler, timeline_with_epochs)
    assert assembler.study_design is None
    assert assembler._errors.count() >= 1


# ---------------------------------------------------------------------------
# _build_elements — undeclared intervention warning
# ---------------------------------------------------------------------------


def test_element_references_unknown_intervention_logs_warning(
    assembler, population_assembler, timeline_with_epochs
):
    errors_before = assembler._errors.count()
    data = {
        "label": "Bad ref",
        "rationale": "r",
        "trial_phase": "Phase II",
        "interventions": [
            {"name": "DrugX", "type": "Drug", "role": "Investigational Treatment"},
        ],
        "elements": [
            # References a valid and an unknown intervention
            {"name": "ElemX", "intervention_names": ["DrugX", "Nonexistent"]},
        ],
    }
    assembler.execute(data, population_assembler, timeline_with_epochs)
    # Design still built; element retained with just the valid intervention
    assert assembler.study_design is not None
    element = assembler.study_design.elements[0]
    assert len(element.studyInterventionIds) == 1
    assert assembler._errors.count() > errors_before


# ---------------------------------------------------------------------------
# _build_cells — unknown arm / epoch / element warnings
# ---------------------------------------------------------------------------


def test_cell_references_unknown_arm_is_skipped(
    assembler, population_assembler, timeline_with_epochs
):
    errors_before = assembler._errors.count()
    data = {
        "label": "Unknown arm cell",
        "rationale": "r",
        "trial_phase": "Phase II",
        "arms": [{"name": "Active", "type": "Experimental"}],
        "cells": [
            {"arm": "Active", "epoch": "Treatment", "elements": []},
            {"arm": "NotAnArm", "epoch": "Treatment", "elements": []},
        ],
    }
    assembler.execute(data, population_assembler, timeline_with_epochs)
    assert assembler.study_design is not None
    # Only one cell survived (the other was skipped with a warning)
    assert len(assembler.study_design.studyCells) == 1
    assert assembler._errors.count() > errors_before


def test_cell_references_unknown_epoch_is_skipped(
    assembler, population_assembler, timeline_with_epochs
):
    errors_before = assembler._errors.count()
    data = {
        "label": "Unknown epoch cell",
        "rationale": "r",
        "trial_phase": "Phase II",
        "arms": [{"name": "Active", "type": "Experimental"}],
        "cells": [
            {"arm": "Active", "epoch": "Treatment", "elements": []},
            {"arm": "Active", "epoch": "NoSuchEpoch", "elements": []},
        ],
    }
    assembler.execute(data, population_assembler, timeline_with_epochs)
    assert assembler.study_design is not None
    assert len(assembler.study_design.studyCells) == 1
    assert assembler._errors.count() > errors_before


def test_cell_references_unknown_element_logs_warning(
    assembler, population_assembler, timeline_with_epochs
):
    errors_before = assembler._errors.count()
    data = {
        "label": "Unknown element cell",
        "rationale": "r",
        "trial_phase": "Phase II",
        "arms": [{"name": "Active", "type": "Experimental"}],
        "elements": [{"name": "Real", "intervention_names": []}],
        "cells": [
            {
                "arm": "Active",
                "epoch": "Treatment",
                # Real is valid, Phantom isn't
                "elements": ["Real", "Phantom"],
            },
        ],
    }
    assembler.execute(data, population_assembler, timeline_with_epochs)
    assert assembler.study_design is not None
    # Single cell built with one valid element reference
    cell = assembler.study_design.studyCells[0]
    assert len(cell.elementIds) == 1
    assert assembler._errors.count() > errors_before


# ---------------------------------------------------------------------------
# _wire_cohorts_to_arms — unknown arm warning
# ---------------------------------------------------------------------------


def test_cohort_references_unknown_arm_logs_warning(
    builder, errors, timeline_with_epochs
):
    pa = PopulationAssembler(builder, errors)
    pa.execute(
        {
            "label": "Pop",
            "inclusion_exclusion": {"inclusion": [], "exclusion": []},
            "cohorts": [
                # Valid arm_name + one unknown
                {"name": "CohortA", "arm_names": ["Active", "Phantom"]},
            ],
        }
    )

    errors_before = errors.count()
    sda = StudyDesignAssembler(builder, errors)
    sda.execute(
        {
            "label": "Cohort unknown arm",
            "rationale": "r",
            "trial_phase": "Phase II",
            "arms": [{"name": "Active", "type": "Experimental"}],
        },
        pa,
        timeline_with_epochs,
    )

    study_design = sda.study_design
    # Cohort's id is still wired to the Active arm
    active = study_design.arms[0]
    assert len(active.populationIds) == 1
    # Warning logged for the phantom arm
    assert errors.count() > errors_before


# ---------------------------------------------------------------------------
# _build_administrations — happy path (dose/route/frequency) & exception
# ---------------------------------------------------------------------------


def test_intervention_with_dose_route_frequency_builds_administration(
    assembler, population_assembler, timeline_with_epochs
):
    """An intervention with dose/route/frequency should produce a populated
    Administration. Exercises the `not (dose or route or frequency)` false
    branch (line 214) plus the Duration/Administration builder calls
    (lines 215-238)."""
    data = {
        "label": "Admin Study",
        "rationale": "r",
        "trial_phase": "Phase II",
        "interventions": [
            {
                "name": "DrugX",
                "type": "Drug",
                "role": "Investigational Treatment",
                "dose": "10 mg",
                "route": "Oral",
                "frequency": "Daily",
            },
        ],
    }
    assembler.execute(data, population_assembler, timeline_with_epochs)
    assert assembler.study_design is not None
    interventions = assembler.study_interventions
    assert len(interventions) == 1
    admins = interventions[0].administrations
    assert len(admins) == 1
    admin = admins[0]
    # Route/frequency should be AliasCode objects populated by the encoder.
    assert admin.route is not None
    assert admin.frequency is not None
    # Duration is a Duration object with null quantity/text by contract.
    assert admin.duration is not None


def test_intervention_with_only_route_still_builds_administration(
    assembler, population_assembler, timeline_with_epochs
):
    """Providing just `route` (no dose/frequency) still triggers the
    admin-build branch. Exercises the `if route else None` false branch
    for the other fields (line 235 else-side)."""
    data = {
        "label": "Admin Study",
        "rationale": "r",
        "trial_phase": "Phase II",
        "interventions": [
            {
                "name": "DrugX",
                "type": "Drug",
                "role": "Investigational Treatment",
                "route": "Oral",
            },
        ],
    }
    assembler.execute(data, population_assembler, timeline_with_epochs)
    interventions = assembler.study_interventions
    assert len(interventions) == 1
    admins = interventions[0].administrations
    assert len(admins) == 1
    assert admins[0].route is not None
    assert admins[0].frequency is None


def test_build_administrations_exception_logged(
    assembler, population_assembler, timeline_with_epochs
):
    """If Builder.create raises mid-administration, _build_administrations
    catches, logs and returns []. Patch the Duration construction path to
    force an exception."""
    errors_before = assembler._errors.count()

    original_create = assembler._builder.create

    def maybe_raise(cls, params):
        # Trigger on Duration creation specifically.
        if cls.__name__ == "Duration":
            raise RuntimeError("forced")
        return original_create(cls, params)

    with patch.object(assembler._builder, "create", side_effect=maybe_raise):
        data = {
            "label": "Admin exc",
            "rationale": "r",
            "trial_phase": "Phase II",
            "interventions": [
                {
                    "name": "DrugX",
                    "type": "Drug",
                    "role": "Investigational Treatment",
                    "dose": "10 mg",
                    "route": "Oral",
                },
            ],
        }
        assembler.execute(data, population_assembler, timeline_with_epochs)

    # Intervention still built (no administration), exception logged.
    assert assembler._errors.count() > errors_before


# ---------------------------------------------------------------------------
# _synthesise_cell_grid — exception handler
# ---------------------------------------------------------------------------


def test_synthesise_cell_grid_exception_logged(
    assembler, population_assembler, timeline_with_epochs
):
    """Force _synthesise_cell_grid's inner builder.create to raise so the
    except clause (lines 432-437) runs. The study design itself is still
    built — cells just end up missing."""
    errors_before = assembler._errors.count()

    original_create = assembler._builder.create
    raised = {"count": 0}

    def maybe_raise(cls, params):
        # Raise only for StudyCell (the synthesis target); let every other
        # create call pass through so the surrounding design assembles.
        if cls.__name__ == "StudyCell":
            raised["count"] += 1
            raise RuntimeError("forced grid failure")
        return original_create(cls, params)

    with patch.object(assembler._builder, "create", side_effect=maybe_raise):
        data = {
            "label": "Grid exc",
            "rationale": "r",
            "trial_phase": "Phase II",
            "arms": [{"name": "A1", "type": "Experimental"}],
            # No cells — synthesis kicks in and fails per-cell.
        }
        assembler.execute(data, population_assembler, timeline_with_epochs)

    # Synthesis attempted (one arm × one epoch = 1 call) and logged.
    assert raised["count"] >= 1
    assert assembler._errors.count() > errors_before


# ---------------------------------------------------------------------------
# _wire_cohorts_to_arms — raw cohort without name / unknown cohort
# ---------------------------------------------------------------------------


def test_wire_cohorts_nameless_raw_is_skipped(builder, errors, timeline_with_epochs):
    """A raw cohort entry with no 'name' key should be silently skipped
    (line 461 early-continue)."""
    pa = PopulationAssembler(builder, errors)
    pa.execute(
        {
            "label": "Pop",
            "inclusion_exclusion": {"inclusion": [], "exclusion": []},
            "cohorts": [{"name": "Real", "arm_names": ["Active"]}],
        }
    )
    # Slip a nameless entry in directly — PopulationAssembler doesn't
    # surface this shape, but _wire_cohorts_to_arms is defensive against
    # it and the defence needs exercising.
    pa._raw_cohorts.append({"arm_names": ["Active"]})  # no 'name'

    sda = StudyDesignAssembler(builder, errors)
    sda.execute(
        {
            "label": "Nameless cohort",
            "rationale": "r",
            "trial_phase": "Phase II",
            "arms": [{"name": "Active", "type": "Experimental"}],
        },
        pa,
        timeline_with_epochs,
    )

    study_design = sda.study_design
    # Nameless raw is skipped; the named "Real" cohort still wires through.
    assert study_design is not None
    assert len(study_design.arms[0].populationIds) == 1


def test_wire_cohorts_unknown_cohort_object_is_skipped(
    builder, errors, timeline_with_epochs
):
    """A raw cohort whose label doesn't match any assembled cohort object
    should be silently skipped (line 466 `if cohort is None: continue`)."""
    pa = PopulationAssembler(builder, errors)
    pa.execute(
        {
            "label": "Pop",
            "inclusion_exclusion": {"inclusion": [], "exclusion": []},
            "cohorts": [{"name": "Real", "arm_names": ["Active"]}],
        }
    )
    # Append a raw entry whose _label_to_name transformation won't match
    # anything in pa.cohorts — simulates a PopulationAssembler that
    # diverged from its raw input.
    pa._raw_cohorts.append({"name": "Phantom", "arm_names": ["Active"]})

    sda = StudyDesignAssembler(builder, errors)
    sda.execute(
        {
            "label": "Phantom cohort",
            "rationale": "r",
            "trial_phase": "Phase II",
            "arms": [{"name": "Active", "type": "Experimental"}],
        },
        pa,
        timeline_with_epochs,
    )

    # Only the real cohort wires — phantom is silently dropped.
    assert len(sda.study_design.arms[0].populationIds) == 1


# ---------------------------------------------------------------------------
# _build_interventions / _build_elements / _build_arms — top-level except
# ---------------------------------------------------------------------------


def test_build_interventions_exception_logged(
    assembler, population_assembler, timeline_with_epochs
):
    """If intervention construction raises at the top level, _build_interventions
    catches, logs and continues (lines 195-200)."""
    errors_before = assembler._errors.count()

    original_create = assembler._builder.create

    def maybe_raise(cls, params):
        if cls.__name__ == "StudyIntervention":
            raise RuntimeError("forced intervention failure")
        return original_create(cls, params)

    with patch.object(assembler._builder, "create", side_effect=maybe_raise):
        data = {
            "label": "Int exc",
            "rationale": "r",
            "trial_phase": "Phase II",
            "interventions": [
                {"name": "DrugX", "type": "Drug", "role": "Investigational Treatment"},
            ],
        }
        assembler.execute(data, population_assembler, timeline_with_epochs)

    assert assembler._errors.count() > errors_before


def test_build_elements_exception_logged(
    assembler, population_assembler, timeline_with_epochs
):
    """Top-level exception handler for element construction (lines 287-292)."""
    errors_before = assembler._errors.count()
    original_create = assembler._builder.create

    def maybe_raise(cls, params):
        if cls.__name__ == "StudyElement":
            raise RuntimeError("forced element failure")
        return original_create(cls, params)

    with patch.object(assembler._builder, "create", side_effect=maybe_raise):
        data = {
            "label": "El exc",
            "rationale": "r",
            "trial_phase": "Phase II",
            "elements": [{"name": "El1", "intervention_names": []}],
        }
        assembler.execute(data, population_assembler, timeline_with_epochs)

    assert assembler._errors.count() > errors_before


def test_build_arms_exception_logged(
    assembler, population_assembler, timeline_with_epochs
):
    """Top-level exception handler for arm construction (lines 325-330)."""
    errors_before = assembler._errors.count()
    original_create = assembler._builder.create

    def maybe_raise(cls, params):
        if cls.__name__ == "StudyArm":
            raise RuntimeError("forced arm failure")
        return original_create(cls, params)

    with patch.object(assembler._builder, "create", side_effect=maybe_raise):
        data = {
            "label": "Arm exc",
            "rationale": "r",
            "trial_phase": "Phase II",
            "arms": [{"name": "Active", "type": "Experimental"}],
        }
        assembler.execute(data, population_assembler, timeline_with_epochs)

    assert assembler._errors.count() > errors_before


def test_build_cells_exception_logged(
    assembler, population_assembler, timeline_with_epochs
):
    """Top-level exception handler for explicit cells (lines 399-404)."""
    errors_before = assembler._errors.count()
    original_create = assembler._builder.create

    def maybe_raise(cls, params):
        if cls.__name__ == "StudyCell":
            raise RuntimeError("forced cell failure")
        return original_create(cls, params)

    with patch.object(assembler._builder, "create", side_effect=maybe_raise):
        data = {
            "label": "Cell exc",
            "rationale": "r",
            "trial_phase": "Phase II",
            "arms": [{"name": "Active", "type": "Experimental"}],
            "cells": [{"arm": "Active", "epoch": "Treatment", "elements": []}],
        }
        assembler.execute(data, population_assembler, timeline_with_epochs)

    assert assembler._errors.count() > errors_before
