"""Tests for MedicalDevice support (GitHub 103).

Covers:
- Device construction: name, label, description, sourcing (decoded,
  undecoded warned, absent)
- Embedded product resolved by name to embeddedProductId; unknown name warned
- Administration -> device linkage by name, unknown reference warned
- DDF00205: an administration whose device embeds its product does not also
  set administrableProductId; a different product is kept
- Devices exposed for StudyVersion via the assembler property
- Exception and None-create handlers
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


def _execute(assembler, population_assembler, timeline_assembler, **overrides):
    data = {
        "label": "Design",
        "rationale": "Rationale",
        "trial_phase": "1",
    }
    data.update(overrides)
    assembler.execute(data, population_assembler, timeline_assembler)
    return assembler


PRODUCTS = [{"name": "Ace Powder"}, {"name": "Other Powder"}]
DEVICES = [{"name": "Ace Inhaler", "embedded_product": "Ace Powder"}]


def _intervention(**admin):
    return [{"name": "Ace", "administrations": [admin]}]


class TestDevices:
    def test_device_built(self, assembler, population_assembler, timeline_assembler):
        a = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            devices=[
                {
                    "name": "Ace Inhaler",
                    "label": "Ace Inhaler Device",
                    "description": "Dry powder inhaler",
                }
            ],
        )
        devices = a.medical_devices
        assert len(devices) == 1
        device = devices[0]
        assert device.name == "ACE-INHALER"
        assert device.label == "Ace Inhaler Device"
        assert device.description == "Dry powder inhaler"
        assert device.embeddedProductId is None
        assert device.sourcing is None

    def test_label_defaults_to_name(
        self, assembler, population_assembler, timeline_assembler
    ):
        a = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            devices=[{"name": "Ace Inhaler"}],
        )
        assert a.medical_devices[0].label == "Ace Inhaler"

    def test_embedded_product_resolved(
        self, assembler, population_assembler, timeline_assembler
    ):
        a = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            products=PRODUCTS,
            devices=DEVICES,
        )
        product = next(p for p in a.administrable_products if p.label == "Ace Powder")
        assert a.medical_devices[0].embeddedProductId == product.id

    def test_unknown_embedded_product_warned(
        self, assembler, population_assembler, timeline_assembler, errors
    ):
        a = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            devices=[{"name": "Ace Inhaler", "embedded_product": "Ghost"}],
        )
        assert a.medical_devices[0].embeddedProductId is None
        assert "embeds undeclared product 'Ghost'" in str(
            errors.to_dict(Errors.WARNING)
        )

    def test_sourcing_decoded(
        self, assembler, population_assembler, timeline_assembler
    ):
        a = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            devices=[{"name": "Ace Inhaler", "sourcing": "Locally Sourced"}],
        )
        assert a.medical_devices[0].sourcing.code == "C215660"

    def test_sourcing_not_decoded_left_unset_with_warning(
        self, assembler, population_assembler, timeline_assembler, errors
    ):
        a = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            devices=[{"name": "Ace Inhaler", "sourcing": "Pharmacy"}],
        )
        assert a.medical_devices[0].sourcing is None
        assert "Sourcing 'Pharmacy'" in str(errors.to_dict(Errors.WARNING))

    def test_no_devices_key_yields_empty_list(
        self, assembler, population_assembler, timeline_assembler
    ):
        a = _execute(assembler, population_assembler, timeline_assembler)
        assert a.medical_devices == []


class TestAdministrationDeviceLink:
    def test_device_embedding_product_clears_product_reference(
        self, assembler, population_assembler, timeline_assembler
    ):  # DDF00205
        a = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            products=PRODUCTS,
            devices=DEVICES,
            interventions=_intervention(
                route="Oral", product_name="Ace Powder", device_name="Ace Inhaler"
            ),
        )
        admin = a.study_interventions[0].administrations[0]
        assert admin.medicalDeviceId == a.medical_devices[0].id
        assert admin.administrableProductId is None

    def test_device_with_other_product_keeps_product_reference(
        self, assembler, population_assembler, timeline_assembler
    ):
        a = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            products=PRODUCTS,
            devices=DEVICES,
            interventions=_intervention(
                route="Oral", product_name="Other Powder", device_name="Ace Inhaler"
            ),
        )
        admin = a.study_interventions[0].administrations[0]
        other = next(p for p in a.administrable_products if p.label == "Other Powder")
        assert admin.medicalDeviceId == a.medical_devices[0].id
        assert admin.administrableProductId == other.id

    def test_device_only(self, assembler, population_assembler, timeline_assembler):
        a = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            products=PRODUCTS,
            devices=DEVICES,
            interventions=_intervention(route="Oral", device_name="Ace Inhaler"),
        )
        admin = a.study_interventions[0].administrations[0]
        assert admin.medicalDeviceId == a.medical_devices[0].id
        assert admin.administrableProductId is None

    def test_unknown_device_reference_warned_and_null(
        self, assembler, population_assembler, timeline_assembler, errors
    ):
        a = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            products=PRODUCTS,
            interventions=_intervention(
                route="Oral", product_name="Ace Powder", device_name="Ghost"
            ),
        )
        admin = a.study_interventions[0].administrations[0]
        assert admin.medicalDeviceId is None
        assert admin.administrableProductId == a.administrable_products[0].id
        assert "undeclared device 'Ghost'" in str(errors.to_dict(Errors.WARNING))

    def test_no_device_reference_stays_null(
        self, assembler, population_assembler, timeline_assembler
    ):
        a = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            interventions=_intervention(route="Oral"),
        )
        assert a.study_interventions[0].administrations[0].medicalDeviceId is None


class TestDeviceExceptions:
    def test_device_creation_exception_logged(
        self, assembler, population_assembler, timeline_assembler, builder, errors
    ):
        original_create = builder.create

        def maybe_raise(cls, params):
            if cls.__name__ == "MedicalDevice":
                raise RuntimeError("forced")
            return original_create(cls, params)

        with patch.object(builder, "create", side_effect=maybe_raise):
            a = _execute(
                assembler,
                population_assembler,
                timeline_assembler,
                devices=[{"name": "Ace Inhaler"}],
            )
        assert a.medical_devices == []
        assert any(
            e["message"].startswith("Failed during creation of device 'Ace Inhaler'")
            for e in errors.to_dict(Errors.DEBUG)
        )

    def test_device_create_none_skipped(
        self, assembler, population_assembler, timeline_assembler, builder
    ):
        original_create = builder.create

        def maybe_none(cls, params):
            if cls.__name__ == "MedicalDevice":
                return None
            return original_create(cls, params)

        with patch.object(builder, "create", side_effect=maybe_none):
            a = _execute(
                assembler,
                population_assembler,
                timeline_assembler,
                devices=[{"name": "Ace Inhaler"}],
            )
        assert a.medical_devices == []
