"""Tests for multi-administration + duration support on StudyDesignAssembler.

Covers:
- ``administrations`` list input: naming (explicit / generated / numbered),
  per-administration route/frequency encoding, duration construction
- Duration: description, will_vary/reason, quantity parsing (value+unit,
  singular retry, unknown-unit fallback onto Duration.text)
- Back-compat: flat dose/route/frequency collapse into one administration
- Exception handler in _build_one_administration
"""

import os
import pathlib
from unittest.mock import patch

import pytest
from simple_error_log.errors import Errors

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
def timeline_assembler(builder, errors):
    ta = TimelineAssembler(builder, errors)
    ta.clear()
    return ta


@pytest.fixture
def assembler(builder, errors):
    return StudyDesignAssembler(builder, errors)


def _execute(assembler, population_assembler, timeline_assembler, interventions):
    assembler.execute(
        {
            "label": "Design",
            "rationale": "Rationale",
            "trial_phase": "1",
            "interventions": interventions,
        },
        population_assembler,
        timeline_assembler,
    )
    return assembler.study_interventions


class TestAdministrationsList:
    def test_multiple_administrations(
        self, assembler, population_assembler, timeline_assembler
    ):
        interventions = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            [
                {
                    "name": "Drug A",
                    "administrations": [
                        {
                            "name": "Oral Dose",
                            "description": "Single oral dose",
                            "route": "Oral",
                            "frequency": "Once",
                        },
                        {"route": "Intravenous"},
                    ],
                }
            ],
        )
        admins = interventions[0].administrations
        assert len(admins) == 2
        assert admins[0].name == "ORAL-DOSE"
        assert admins[0].label == "Oral Dose"
        assert admins[0].description == "Single oral dose"
        assert admins[0].route.standardCode.decode == "Oral Route of Administration"
        assert admins[0].frequency is not None
        # Unnamed second administration gets a numbered generated name.
        assert admins[1].name == "ADM-DRUG-A-2"
        assert admins[1].frequency is None

    def test_single_unnamed_administration_unnumbered(
        self, assembler, population_assembler, timeline_assembler
    ):
        interventions = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            [{"name": "Drug A", "administrations": [{"route": "Oral"}]}],
        )
        admins = interventions[0].administrations
        assert len(admins) == 1
        assert admins[0].name == "ADM-DRUG-A"

    def test_duration_with_parsed_quantity(
        self, assembler, population_assembler, timeline_assembler
    ):
        interventions = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            [
                {
                    "name": "Drug A",
                    "administrations": [
                        {
                            "route": "Intravenous",
                            "duration": {
                                "description": "IV bolus over 1 minute",
                                "quantity": "1 min",
                            },
                        }
                    ],
                }
            ],
        )
        duration = interventions[0].administrations[0].duration
        assert duration.text == "IV bolus over 1 minute"
        assert duration.quantity.value == 1.0
        assert duration.quantity.unit.standardCode.decode == "Minute"
        assert duration.durationWillVary is False
        assert duration.reasonDurationWillVary is None

    def test_duration_singular_unit_retry(
        self, assembler, population_assembler, timeline_assembler
    ):
        # "minutes" is not in CT; the singular "minute" is.
        interventions = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            [
                {
                    "name": "Drug A",
                    "administrations": [{"duration": {"quantity": "5 minutes"}}],
                }
            ],
        )
        duration = interventions[0].administrations[0].duration
        assert duration.quantity.value == 5.0
        assert duration.quantity.unit.standardCode.decode == "Minute"

    def test_duration_will_vary(
        self, assembler, population_assembler, timeline_assembler
    ):
        interventions = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            [
                {
                    "name": "Drug A",
                    "administrations": [
                        {
                            "duration": {
                                "will_vary": True,
                                "will_vary_reason": "Adaptive dosing",
                            }
                        }
                    ],
                }
            ],
        )
        duration = interventions[0].administrations[0].duration
        assert duration.durationWillVary is True
        assert duration.reasonDurationWillVary == "Adaptive dosing"
        assert duration.quantity is None
        assert duration.text is None

    def test_duration_unknown_unit_falls_back_to_text(
        self, assembler, population_assembler, timeline_assembler
    ):
        interventions = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            [
                {
                    "name": "Drug A",
                    "administrations": [
                        {
                            "duration": {
                                "description": "Weird duration",
                                "quantity": "2 elephants",
                            }
                        }
                    ],
                }
            ],
        )
        duration = interventions[0].administrations[0].duration
        assert duration.quantity is None
        assert duration.text == "Weird duration (2 elephants)"

    def test_duration_unparseable_quantity_without_description(
        self, assembler, population_assembler, timeline_assembler
    ):
        interventions = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            [
                {
                    "name": "Drug A",
                    "administrations": [
                        {"duration": {"quantity": "until progression"}}
                    ],
                }
            ],
        )
        duration = interventions[0].administrations[0].duration
        assert duration.quantity is None
        assert duration.text == "until progression"

    def test_administration_creation_exception_logged(
        self, assembler, population_assembler, timeline_assembler, builder
    ):
        original_create = builder.create

        def maybe_raise(cls, params):
            if cls.__name__ == "Administration":
                raise RuntimeError("forced")
            return original_create(cls, params)

        with patch.object(builder, "create", side_effect=maybe_raise):
            interventions = _execute(
                assembler,
                population_assembler,
                timeline_assembler,
                [{"name": "Drug A", "administrations": [{"route": "Oral"}]}],
            )
        assert interventions[0].administrations == []


class TestFlatBackCompat:
    def test_flat_fields_collapse_to_single_administration(
        self, assembler, population_assembler, timeline_assembler
    ):
        interventions = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            [
                {
                    "name": "Flat Drug",
                    "dose": "10 mg",
                    "route": "Oral",
                    "frequency": "Once",
                }
            ],
        )
        admins = interventions[0].administrations
        assert len(admins) == 1
        assert admins[0].name == "ADM-FLAT-DRUG"
        assert admins[0].route is not None
        assert admins[0].frequency is not None
        # Placeholder duration, as before.
        assert admins[0].duration.quantity is None
        assert admins[0].duration.durationWillVary is False

    def test_no_administration_data_yields_empty_list(
        self, assembler, population_assembler, timeline_assembler
    ):
        interventions = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            [{"name": "Bare Drug"}],
        )
        assert interventions[0].administrations == []
