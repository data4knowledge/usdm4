"""Assembler branches the scenario tests do not reach: an empty section
reference line, an enrollment that fails to build, a role party that fails
to build, a male-only population, and the study design exception handlers
for indications, control type, a plain create and model provenance, plus a
participation duration with nothing to record."""

import os
import pathlib
from unittest.mock import patch

import pytest
from simple_error_log.errors import Errors

from src.usdm4.api.extension import ExtensionAttribute
from src.usdm4.api.indication import Indication
from src.usdm4.api.study_epoch import StudyEpoch
from src.usdm4.assembler.amendments_assembler import AmendmentsAssembler
from src.usdm4.assembler.identification_assembler import IdentificationAssembler
from src.usdm4.assembler.population_assembler import PopulationAssembler
from src.usdm4.assembler.study_design_assembler import StudyDesignAssembler
from src.usdm4.builder.builder import Builder


def _root_path():
    base = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


@pytest.fixture(scope="module")
def builder():
    return Builder(_root_path(), Errors())


@pytest.fixture
def errors():
    return Errors()


def _messages(errors: Errors, level=Errors.DEBUG) -> list[str]:
    return [e["message"] for e in errors.to_dict(level=level)]


def _raising(builder, klass):
    original = builder.create

    def create(cls, params, *args, **kwargs):
        if cls.__name__ == klass.__name__:  # src.usdm4 and usdm4 classes
            raise RuntimeError("forced")
        return original(cls, params, *args, **kwargs)

    return create


class TestAmendments:
    def test_empty_section_line(self, builder, errors):
        builder.clear()
        assert AmendmentsAssembler(builder, errors)._parse_section_line("   ") == []

    def test_enrollment_failure_logged(self, builder, errors):
        builder.clear()
        assembler = AmendmentsAssembler(builder, errors)
        with patch.object(
            assembler, "_enrollment_geographic_scope", side_effect=RuntimeError("x")
        ):
            assert (
                assembler._create_enrollment({"enrollment": {"value": 5, "unit": "%"}})
                is None
            )
        assert any(
            m.startswith("Failed during creation of enrollments")
            for m in _messages(errors)
        )


class TestIdentification:
    def test_role_party_without_name_logged(self, builder, errors):
        builder.clear()
        assembler = IdentificationAssembler(builder, errors)
        assembler.execute({"roles": {"co_sponsor": {"address": {}}}})
        assert any(
            m.startswith("Failed during creation of organization in co_sponsor")
            for m in _messages(errors)
        )

    def test_party_not_created_is_an_error(self, builder, errors):
        builder.clear()
        assembler = IdentificationAssembler(builder, errors)
        with patch.object(assembler, "_create_organization", return_value=None):
            assembler.execute({"roles": {"co_sponsor": {"name": "Co Ltd"}}})
        found = [
            e
            for e in errors.to_dict(level=Errors.DEBUG)
            if e["message"].startswith("Failed to create organization in co_sponsor")
        ]
        assert found and found[0]["level"] == "Error"
        assert found[0]["location"]["method_name"] == "execute"


class TestPopulation:
    def test_male_only(self, builder, errors):
        builder.clear()
        sex = PopulationAssembler(builder, errors)._build_planned_sex({"sex": "male"})
        assert [s.decode for s in sex] == ["Male"]


class TestStudyDesign:
    @pytest.fixture
    def assembler(self, builder, errors):
        builder.clear()
        return StudyDesignAssembler(builder, errors)

    def test_indication_failure_logged(self, assembler, builder, errors):
        with patch.object(builder, "create", side_effect=_raising(builder, Indication)):
            assert assembler._build_indications(["Asthma"]) == []
        assert any(
            m.startswith("Failed during creation of indication 'Asthma'")
            for m in _messages(errors)
        )

    def test_control_type_failure_logged(self, assembler, builder, errors):
        with patch.object(
            builder, "create", side_effect=_raising(builder, ExtensionAttribute)
        ):
            assert assembler._control_type_extensions("Placebo") == []
        assert any(
            m.startswith("Failed during creation of control type 'Placebo'")
            for m in _messages(errors)
        )

    def test_create_failure_logged(self, assembler, builder, errors):
        with patch.object(builder, "create", side_effect=_raising(builder, StudyEpoch)):
            assert assembler._create(StudyEpoch, {}) is None
        assert any(
            m.startswith("Failed during creation of StudyEpoch")
            for m in _messages(errors)
        )

    def test_participation_duration_with_nothing_to_record(self, assembler, errors):
        assembler._set_participation_duration({"description": "Some text"}, [])
        assert _messages(errors, Errors.WARNING) == []

    def test_model_provenance_failure_logged(self, assembler, builder, errors):
        with patch.object(
            builder, "create", side_effect=_raising(builder, ExtensionAttribute)
        ):
            assert assembler._model_extensions(None) == []
        assert any(
            m.startswith("Failed during creation of intervention model provenance")
            for m in _messages(errors)
        )
