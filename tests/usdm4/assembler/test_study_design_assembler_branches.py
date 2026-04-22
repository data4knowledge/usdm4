"""Branch-coverage supplements for StudyDesignAssembler.

The wiring tests in test_study_design_assembler.py cover the happy
paths. These hit the lower-traffic warning branches:

- Element referencing an undeclared intervention
- Cell referencing an unknown arm / epoch / element
- Cohort with arm_names referencing an unknown arm
- execute() top-level exception handler
"""

import os
import pathlib

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
