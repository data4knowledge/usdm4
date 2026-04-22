"""Branch-coverage supplements for PopulationAssembler.

The main test_population_assembler.py covers the happy paths; these
tests target the lower-traffic branches:

- execute() top-level exception handler
- Unknown sex value (falls through to encoder)
- Partial age range (min only, max only)
- Non-numeric top-level planned_enrollment
- Non-numeric cohort planned_enrollment (both cohort-enrollment and sum paths)
- Cohort missing name
- Cohort missing entirely / non-dict cohort
"""

import os
import pathlib

import pytest
from simple_error_log.errors import Errors

from src.usdm4.assembler.population_assembler import PopulationAssembler
from src.usdm4.builder.builder import Builder


def _root_path():
    base = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


@pytest.fixture
def assembler():
    builder = Builder(_root_path(), Errors())
    builder.clear()
    return PopulationAssembler(builder, Errors())


def _base_data(**overrides):
    base = {
        "label": "Study Population",
        "inclusion_exclusion": {"inclusion": [], "exclusion": []},
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# execute() top-level exception handler
# ---------------------------------------------------------------------------


def test_execute_missing_inclusion_exclusion_is_logged(assembler):
    """Missing 'inclusion_exclusion' raises KeyError inside _ie — caught and
    logged at the execute() boundary."""
    assembler.execute({"label": "X"})  # no inclusion_exclusion
    # Population not created; exception recorded
    assert assembler.population is None
    assert assembler._errors.count() >= 1


def test_execute_empty_data_logs_info_and_returns(assembler):
    """Empty input data hits the early-return 'no data' info branch."""
    assembler.execute({})
    assert assembler.population is None


# ---------------------------------------------------------------------------
# Sex fallthrough
# ---------------------------------------------------------------------------


def test_unknown_sex_falls_through_to_encoder(assembler):
    data = _base_data(demographics={"sex": "UNKNOWN"})
    assembler.execute(data)
    # Population still builds; the encoder will have logged a warning for the
    # unknown sex value, so there should be errors collected.
    assert assembler.population is not None
    # plannedSex list has a single entry (the fallthrough path)
    assert len(assembler.population.plannedSex) == 1


# ---------------------------------------------------------------------------
# Partial age range
# ---------------------------------------------------------------------------


def test_partial_age_range_min_only_logs_warning(assembler):
    data = _base_data(demographics={"age_min": 18, "age_unit": "Years"})
    assembler.execute(data)
    assert assembler.population is not None
    assert assembler._errors.count() >= 1
    # Range is present; missing max filled with min
    age_range = assembler.population.plannedAge
    assert age_range is not None
    assert age_range.minValue.value == 18.0
    assert age_range.maxValue.value == 18.0


def test_partial_age_range_max_only_logs_warning(assembler):
    data = _base_data(demographics={"age_max": 65, "age_unit": "Years"})
    assembler.execute(data)
    assert assembler.population is not None
    age_range = assembler.population.plannedAge
    assert age_range is not None
    assert age_range.minValue.value == 65.0
    assert age_range.maxValue.value == 65.0


def test_no_age_range_returns_none(assembler):
    data = _base_data(demographics={"sex": "ALL"})
    assembler.execute(data)
    assert assembler.population is not None
    assert assembler.population.plannedAge is None


# ---------------------------------------------------------------------------
# Planned enrollment non-numeric handling
# ---------------------------------------------------------------------------


def test_non_numeric_explicit_planned_enrollment_logs_warning(assembler):
    data = _base_data(planned_enrollment="not-a-number")
    assembler.execute(data)
    assert assembler.population is not None
    assert assembler.population.plannedEnrollmentNumber is None
    assert assembler._errors.count() >= 1


def test_non_numeric_cohort_enrollment_in_sum_is_skipped(assembler):
    data = _base_data(
        cohorts=[
            {"name": "A", "planned_enrollment": 10},
            {"name": "B", "planned_enrollment": "oops"},
            {"name": "C", "planned_enrollment": 20},
        ]
    )
    assembler.execute(data)
    assert assembler.population is not None
    # Total should be 30 (10 + 20); the non-numeric entry is skipped with
    # a warning.
    assert assembler.population.plannedEnrollmentNumber is not None
    assert assembler.population.plannedEnrollmentNumber.value == 30.0
    assert assembler._errors.count() >= 1


def test_non_numeric_cohort_enrollment_on_cohort_itself(assembler):
    """Cohort's _cohort_enrollment path with bad value → warning + None."""
    data = _base_data(
        cohorts=[
            {"name": "A", "planned_enrollment": "broken"},
        ]
    )
    assembler.execute(data)
    assert assembler.population is not None
    # The single cohort should have no enrollment number
    assert assembler.cohorts[0].plannedEnrollmentNumber is None


def test_all_cohorts_without_enrollment_results_in_none(assembler):
    """When cohorts exist but none supply planned_enrollment, the sum branch
    still falls through to None via the `seen` gate."""
    data = _base_data(cohorts=[{"name": "A"}, {"name": "B"}])
    assembler.execute(data)
    assert assembler.population is not None
    assert assembler.population.plannedEnrollmentNumber is None


# ---------------------------------------------------------------------------
# Cohort edge cases
# ---------------------------------------------------------------------------


def test_cohort_missing_name_is_skipped_with_warning(assembler):
    data = _base_data(
        cohorts=[
            {"name": "Valid"},
            {"name": ""},  # empty name → warning
            {"label": "NoName"},  # no name key → warning
        ]
    )
    assembler.execute(data)
    assert assembler.population is not None
    # Only the valid cohort builds
    assert len(assembler.cohorts) == 1
    assert assembler._errors.count() >= 2  # two skipped cohorts


def test_non_dict_cohort_is_skipped(assembler):
    """A cohort entry that isn't a dict is silently skipped (no warning)."""
    data = _base_data(
        cohorts=[
            {"name": "A"},
            "not a dict",
            None,
        ]
    )
    assembler.execute(data)
    assert assembler.population is not None
    assert len(assembler.cohorts) == 1
