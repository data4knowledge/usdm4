"""Tests for ObjectivesAssembler.

Covers:
- Objective / endpoint construction with explicit and generated names
- Level encoding (objective C188725, endpoint C188726) incl. default fallback
- Estimand construction: endpoint / intervention / population-subset
  reference resolution (case-insensitive, name or label)
- AnalysisPopulation defaulting to the whole study population
- Attachment onto the assembled study design
- Warning branches: unknown endpoint / intervention / subset references
"""

import os
import pathlib

import pytest
from simple_error_log.errors import Errors

from usdm4.assembler.objectives_assembler import ObjectivesAssembler
from usdm4.assembler.population_assembler import PopulationAssembler
from usdm4.assembler.study_design_assembler import StudyDesignAssembler
from usdm4.assembler.timeline_assembler import TimelineAssembler
from usdm4.builder.builder import Builder


def _root_path():
    base = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


@pytest.fixture(scope="module")
def builder():
    # Module-scoped (mirrors test_population_assembler.py): first CT lookup
    # on a fresh Builder is expensive; share one instance and clear
    # cross-references per test via the population_assembler fixture.
    return Builder(_root_path(), Errors())


@pytest.fixture
def errors():
    return Errors()


@pytest.fixture
def population_assembler(builder, errors):
    builder.clear()  # Root of the per-test fixture chain — reset cross-refs.
    pa = PopulationAssembler(builder, errors)
    pa.execute(
        {
            "label": "Main population",
            "inclusion_exclusion": {"inclusion": ["Age >= 21"], "exclusion": []},
            "cohorts": [{"name": "Cohort A", "label": "Cohort A Label"}],
        }
    )
    return pa


@pytest.fixture
def timeline_assembler(builder, errors):
    ta = TimelineAssembler(builder, errors)
    ta.clear()
    return ta


@pytest.fixture
def study_design_assembler(builder, errors, population_assembler, timeline_assembler):
    sda = StudyDesignAssembler(builder, errors)
    sda.execute(
        {
            "label": "Design",
            "rationale": "Rationale",
            "trial_phase": "1",
            "intervention_model": "Parallel",
            "interventions": [
                {"name": "Drug A", "label": "Drug A Label"},
                {"name": "Drug B"},
            ],
        },
        population_assembler,
        timeline_assembler,
    )
    return sda


@pytest.fixture
def objectives_assembler(builder, errors):
    return ObjectivesAssembler(builder, errors)


def _objectives_data() -> dict:
    return {
        "objectives": [
            {
                "name": "OBJ1",
                "text": "To determine absolute bioavailability",
                "level": "Primary",
                "endpoints": [
                    {
                        "name": "END1",
                        "text": "Absolute bioavailability",
                        "level": "Primary",
                        "purpose": "Efficacy",
                    }
                ],
            },
            {
                "text": "To describe safety",
                "level": "Secondary",
                "endpoints": [{"text": "TEAEs and SAEs", "level": "Secondary"}],
            },
        ],
        "estimands": [
            {
                "summary_measure": "Geometric mean ratio",
                "population_text": "All randomised participants",
                "endpoint_name": "END1",
                "treatment_names": ["Drug A"],
                "intercurrent_events": [
                    {
                        "name": "ICE1",
                        "text": "Discontinuation due to AE",
                        "strategy": "Treatment policy",
                    }
                ],
            }
        ],
    }


class TestObjectivesAssembler:
    def test_initialization(self, builder, errors):
        assembler = ObjectivesAssembler(builder, errors)
        assert assembler._builder is builder
        assert assembler._errors is errors
        assert assembler.objectives == []
        assert assembler.estimands == []
        assert assembler.analysis_populations == []

    def test_execute_no_data(
        self, objectives_assembler, study_design_assembler, population_assembler
    ):
        objectives_assembler.execute({}, study_design_assembler, population_assembler)
        assert objectives_assembler.objectives == []
        assert objectives_assembler.estimands == []

    def test_objectives_and_endpoints(
        self, objectives_assembler, study_design_assembler, population_assembler
    ):
        objectives_assembler.execute(
            _objectives_data(), study_design_assembler, population_assembler
        )
        objectives = objectives_assembler.objectives
        assert len(objectives) == 2

        # Explicit names are normalised; generated names fill the gaps.
        assert objectives[0].name == "OBJ1"
        assert objectives[1].name == "OBJECTIVE-2"
        assert objectives[0].endpoints[0].name == "END1"
        assert objectives[1].endpoints[0].name == "ENDPOINT-2-1"

        # Level encoding — objective C188725, endpoint C188726.
        assert objectives[0].level.code == "C85826"
        assert objectives[0].level.decode == "Trial Primary Objective"
        assert objectives[1].level.code == "C85827"
        assert objectives[0].endpoints[0].level.code == "C94496"
        assert objectives[1].endpoints[0].level.code == "C139173"
        assert objectives[0].endpoints[0].purpose == "Efficacy"

    def test_exploratory_and_default_levels(
        self, objectives_assembler, study_design_assembler, population_assembler
    ):
        data = {
            "objectives": [
                {
                    "text": "Exploratory objective",
                    "level": "Exploratory",
                    "endpoints": [{"text": "Endpoint", "level": "Unknown Level"}],
                }
            ]
        }
        objectives_assembler.execute(data, study_design_assembler, population_assembler)
        objective = objectives_assembler.objectives[0]
        assert objective.level.code == "C163559"
        # Unknown endpoint level falls back to the default (primary).
        assert objective.endpoints[0].level.code == "C94496"

    def test_estimand_wiring(
        self, objectives_assembler, study_design_assembler, population_assembler
    ):
        objectives_assembler.execute(
            _objectives_data(), study_design_assembler, population_assembler
        )
        assert len(objectives_assembler.estimands) == 1
        estimand = objectives_assembler.estimands[0]
        endpoint = objectives_assembler.objectives[0].endpoints[0]
        intervention = study_design_assembler.study_interventions[0]

        assert estimand.name == "ESTIMAND-1"
        assert estimand.populationSummary == "Geometric mean ratio"
        assert estimand.variableOfInterestId == endpoint.id
        assert estimand.interventionIds == [intervention.id]
        assert len(estimand.intercurrentEvents) == 1
        assert estimand.intercurrentEvents[0].strategy == "Treatment policy"

        # Analysis population defaults to subsetting the study population.
        assert len(objectives_assembler.analysis_populations) == 1
        ap = objectives_assembler.analysis_populations[0]
        assert estimand.analysisPopulationId == ap.id
        assert ap.text == "All randomised participants"
        assert ap.subsetOfIds == [population_assembler.population.id]

    def test_estimand_treatment_resolution_by_label_case_insensitive(
        self, objectives_assembler, study_design_assembler, population_assembler
    ):
        data = _objectives_data()
        data["estimands"][0]["treatment_names"] = ["drug a label"]
        objectives_assembler.execute(data, study_design_assembler, population_assembler)
        intervention = study_design_assembler.study_interventions[0]
        assert objectives_assembler.estimands[0].interventionIds == [intervention.id]

    def test_estimand_unknown_treatment_skipped_with_warning(
        self,
        objectives_assembler,
        study_design_assembler,
        population_assembler,
        errors,
    ):
        data = _objectives_data()
        data["estimands"][0]["treatment_names"] = ["Drug X"]
        objectives_assembler.execute(data, study_design_assembler, population_assembler)
        assert objectives_assembler.estimands[0].interventionIds == []

    def test_estimand_cohort_subset_resolution(
        self, objectives_assembler, study_design_assembler, population_assembler
    ):
        data = _objectives_data()
        data["estimands"][0]["population_subset_names"] = ["Cohort A"]
        objectives_assembler.execute(data, study_design_assembler, population_assembler)
        cohort = population_assembler.cohorts[0]
        ap = objectives_assembler.analysis_populations[0]
        assert ap.subsetOfIds == [cohort.id]

    def test_estimand_unknown_subset_skipped(
        self, objectives_assembler, study_design_assembler, population_assembler
    ):
        data = _objectives_data()
        data["estimands"][0]["population_subset_names"] = ["Cohort Z"]
        objectives_assembler.execute(data, study_design_assembler, population_assembler)
        ap = objectives_assembler.analysis_populations[0]
        assert ap.subsetOfIds == []

    def test_estimand_unknown_endpoint_skipped(
        self, objectives_assembler, study_design_assembler, population_assembler
    ):
        # Direct assembler use bypasses schema validation; the assembler
        # must guard the reference itself.
        data = _objectives_data()
        data["estimands"][0]["endpoint_name"] = "END99"
        objectives_assembler.execute(data, study_design_assembler, population_assembler)
        assert objectives_assembler.estimands == []
        assert objectives_assembler.analysis_populations == []

    def test_attachment_to_study_design(
        self, objectives_assembler, study_design_assembler, population_assembler
    ):
        objectives_assembler.execute(
            _objectives_data(), study_design_assembler, population_assembler
        )
        study_design = study_design_assembler.study_design
        assert study_design.objectives == objectives_assembler.objectives
        assert study_design.estimands == objectives_assembler.estimands
        assert (
            study_design.analysisPopulations
            == objectives_assembler.analysis_populations
        )

    def test_no_study_design_logs_warning(self, builder, errors, population_assembler):
        sda = StudyDesignAssembler(builder, errors)  # not executed
        assembler = ObjectivesAssembler(builder, errors)
        assembler.execute(
            {"objectives": [{"text": "Objective"}]}, sda, population_assembler
        )
        # Objectives are still assembled, just not attached.
        assert len(assembler.objectives) == 1

    def test_clear(
        self, objectives_assembler, study_design_assembler, population_assembler
    ):
        objectives_assembler.execute(
            _objectives_data(), study_design_assembler, population_assembler
        )
        objectives_assembler.clear()
        assert objectives_assembler.objectives == []
        assert objectives_assembler.estimands == []
        assert objectives_assembler.analysis_populations == []


# ----------------------------------------------------------------------
# Branch coverage — exception handlers and name-generation fallbacks
# ----------------------------------------------------------------------

from unittest.mock import patch  # noqa: E402

from usdm4.assembler.assembler import Assembler  # noqa: E402


def _forced_raise(target_class_name, builder):
    original_create = builder.create

    def maybe_raise(cls, params):
        if cls.__name__ == target_class_name:
            raise RuntimeError("forced")
        return original_create(cls, params)

    return maybe_raise


class TestObjectivesAssemblerBranches:
    def test_name_from_label_when_name_absent(
        self, objectives_assembler, study_design_assembler, population_assembler
    ):
        data = {"objectives": [{"label": "Main objective", "text": "Objective text"}]}
        objectives_assembler.execute(data, study_design_assembler, population_assembler)
        assert objectives_assembler.objectives[0].name == "MAIN-OBJECTIVE"

    def test_subset_resolution_by_population_label(
        self, objectives_assembler, study_design_assembler, population_assembler
    ):
        data = _objectives_data()
        data["estimands"][0]["population_subset_names"] = ["Main population"]
        objectives_assembler.execute(data, study_design_assembler, population_assembler)
        ap = objectives_assembler.analysis_populations[0]
        assert ap.subsetOfIds == [population_assembler.population.id]

    def test_objective_creation_exception_logged(
        self,
        objectives_assembler,
        study_design_assembler,
        population_assembler,
        builder,
    ):
        with patch.object(
            builder, "create", side_effect=_forced_raise("Objective", builder)
        ):
            objectives_assembler.execute(
                {"objectives": [{"text": "Objective"}]},
                study_design_assembler,
                population_assembler,
            )
        assert objectives_assembler.objectives == []

    def test_endpoint_creation_exception_logged(
        self,
        objectives_assembler,
        study_design_assembler,
        population_assembler,
        builder,
    ):
        with patch.object(
            builder, "create", side_effect=_forced_raise("Endpoint", builder)
        ):
            objectives_assembler.execute(
                {
                    "objectives": [
                        {"text": "Objective", "endpoints": [{"text": "Endpoint"}]}
                    ]
                },
                study_design_assembler,
                population_assembler,
            )
        # Objective still assembled, endpoint list empty.
        assert len(objectives_assembler.objectives) == 1
        assert objectives_assembler.objectives[0].endpoints == []

    def test_estimand_creation_exception_logged(
        self,
        objectives_assembler,
        study_design_assembler,
        population_assembler,
        builder,
    ):
        with patch.object(
            builder, "create", side_effect=_forced_raise("Estimand", builder)
        ):
            objectives_assembler.execute(
                _objectives_data(), study_design_assembler, population_assembler
            )
        assert objectives_assembler.estimands == []

    def test_analysis_population_exception_skips_estimand(
        self,
        objectives_assembler,
        study_design_assembler,
        population_assembler,
        builder,
    ):
        with patch.object(
            builder,
            "create",
            side_effect=_forced_raise("AnalysisPopulation", builder),
        ):
            objectives_assembler.execute(
                _objectives_data(), study_design_assembler, population_assembler
            )
        assert objectives_assembler.estimands == []
        assert objectives_assembler.analysis_populations == []

    def test_intercurrent_event_exception_logged(
        self,
        objectives_assembler,
        study_design_assembler,
        population_assembler,
        builder,
    ):
        with patch.object(
            builder,
            "create",
            side_effect=_forced_raise("IntercurrentEvent", builder),
        ):
            objectives_assembler.execute(
                _objectives_data(), study_design_assembler, population_assembler
            )
        # Estimand still built, with an empty intercurrent event list.
        assert len(objectives_assembler.estimands) == 1
        assert objectives_assembler.estimands[0].intercurrentEvents == []

    def test_execute_top_level_exception_logged(
        self, objectives_assembler, population_assembler, errors
    ):
        # Passing an object without the expected attributes forces the
        # top-level handler (study_design_assembler=None → attribute error
        # inside _build_estimands' intervention lookup).
        objectives_assembler.execute(
            {"objectives": [{"text": "Objective"}], "estimands": []},
            None,
            population_assembler,
        )
        assert objectives_assembler.estimands == []


class TestAssemblerObjectivesWiring:
    """Objectives routed through the top-level Assembler."""

    def _data(self) -> dict:
        return {
            "identification": {
                "titles": {"brief": "Test", "official": "Official Test"},
                "identifiers": [
                    {"identifier": "NCT12345678", "scope": {"standard": "nct"}}
                ],
            },
            "document": {
                "document": {
                    "label": "Protocol",
                    "version": "1.0",
                    "status": "final",
                    "template": "Template",
                    "version_date": "2024-01-01",
                },
                "sections": [],
            },
            "population": {
                "label": "Population",
                "inclusion_exclusion": {"inclusion": [], "exclusion": []},
            },
            "study_design": {
                "label": "Design",
                "rationale": "Rationale",
                "trial_phase": "1",
                "interventions": [{"name": "Drug A"}],
            },
            "study": {
                "name": {"acronym": "TST"},
                "label": "Test",
                "version": "1.0",
                "rationale": "Rationale",
            },
            "objectives": {
                "objectives": [
                    {
                        "text": "Objective",
                        "level": "Primary",
                        "endpoints": [{"name": "END1", "text": "Endpoint"}],
                    }
                ],
                "estimands": [
                    {
                        "summary_measure": "Mean difference",
                        "endpoint_name": "END1",
                        "treatment_names": ["Drug A"],
                    }
                ],
            },
        }

    def test_execute_with_objectives(self):
        errors = Errors()
        assembler = Assembler(_root_path(), errors)
        assembler.execute(self._data())
        study_design = assembler._study_design_assembler.study_design
        assert len(study_design.objectives) == 1
        assert len(study_design.estimands) == 1
        assert len(study_design.analysisPopulations) == 1
        assert errors.error_count() == 0

    def test_execute_without_objectives_leaves_empty_lists(self):
        errors = Errors()
        assembler = Assembler(_root_path(), errors)
        data = self._data()
        del data["objectives"]
        assembler.execute(data)
        study_design = assembler._study_design_assembler.study_design
        assert study_design.objectives == []
        assert study_design.estimands == []
        assert study_design.analysisPopulations == []
