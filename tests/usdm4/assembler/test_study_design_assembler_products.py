"""Tests for AdministrableProduct / Substance support (issue 48).

Covers:
- Product construction: dose form + product designation CT resolution and
  warned fallbacks (Unknown / IMP)
- Ingredients: one Active-Ingredient per substance (NCI other-code role)
- Strength parsing: "10 mg", "50 mg/5 mL", "50 mg/mL" (unit-only
  denominator), unparseable dropped with warning
- Administration -> product linkage by name, unknown reference warned
- Products flow to StudyVersion via the assembler property
- Exception handlers
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


class TestProducts:
    def test_product_with_ct_resolution(
        self, assembler, population_assembler, timeline_assembler
    ):
        a = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            products=[
                {
                    "name": "Drug A Tablet",
                    "label": "Drug A 10 mg Tablet",
                    "dose_form": "Tablet",
                    "product_designation": "IMP",
                }
            ],
        )
        products = a.administrable_products
        assert len(products) == 1
        product = products[0]
        assert product.name == "DRUG-A-TABLET"
        assert product.label == "Drug A 10 mg Tablet"
        assert product.administrableDoseForm.standardCode.code == "C42998"
        assert product.productDesignation.code == "C202579"

    def test_unresolvable_ct_falls_back_with_warning(
        self, assembler, population_assembler, timeline_assembler, errors
    ):
        a = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            products=[
                {
                    "name": "Odd",
                    "dose_form": "Hologram",
                    "product_designation": "Mystery",
                }
            ],
        )
        product = a.administrable_products[0]
        assert product.administrableDoseForm.standardCode.decode == "Unknown"
        assert product.productDesignation.decode == "Investigational Medicinal Product"
        messages = str(errors.to_dict(Errors.WARNING))
        assert "Dose form 'Hologram'" in messages
        assert "Product designation 'Mystery'" in messages

    def test_empty_dose_form_and_designation_default(
        self, assembler, population_assembler, timeline_assembler
    ):
        a = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            products=[{"name": "Bare"}],
        )
        product = a.administrable_products[0]
        assert product.administrableDoseForm.standardCode.decode == "Unknown"
        assert product.productDesignation.code == "C202579"

    def test_no_products_key_yields_empty_list(
        self, assembler, population_assembler, timeline_assembler
    ):
        a = _execute(assembler, population_assembler, timeline_assembler)
        assert a.administrable_products == []


class TestIngredientsAndStrengths:
    def _product(self, assembler, population_assembler, timeline_assembler, substances):
        a = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            products=[{"name": "P", "substances": substances}],
        )
        return a.administrable_products[0]

    def test_active_ingredient_per_substance(
        self, assembler, population_assembler, timeline_assembler
    ):
        product = self._product(
            assembler,
            population_assembler,
            timeline_assembler,
            [{"name": "Substance One"}, {"name": "Substance Two"}],
        )
        assert len(product.ingredients) == 2
        role = product.ingredients[0].role
        assert role.code == "C82533"
        assert role.decode == "Active Ingredient"
        assert product.ingredients[0].substance.name == "SUBSTANCE-ONE"

    def test_numerator_only_strength(
        self, assembler, population_assembler, timeline_assembler
    ):
        product = self._product(
            assembler,
            population_assembler,
            timeline_assembler,
            [{"name": "S", "strength": "10 mg"}],
        )
        strength = product.ingredients[0].substance.strengths[0]
        assert strength.numerator.value == 10.0
        assert strength.numerator.unit.standardCode.decode == "Milligram"
        assert strength.denominator is None
        assert strength.label == "10 mg"

    def test_numerator_denominator_strength(
        self, assembler, population_assembler, timeline_assembler
    ):
        product = self._product(
            assembler,
            population_assembler,
            timeline_assembler,
            [{"name": "S", "strength": "50 mg/5 mL"}],
        )
        strength = product.ingredients[0].substance.strengths[0]
        assert strength.numerator.value == 50.0
        assert strength.denominator.value == 5.0
        assert strength.denominator.unit.standardCode.decode == "Milliliter"

    def test_unit_only_denominator(
        self, assembler, population_assembler, timeline_assembler
    ):
        product = self._product(
            assembler,
            population_assembler,
            timeline_assembler,
            [{"name": "S", "strength": "50 mg/mL"}],
        )
        strength = product.ingredients[0].substance.strengths[0]
        assert strength.numerator.value == 50.0
        assert strength.denominator.value == 1.0
        assert strength.denominator.unit.standardCode.decode == "Milliliter"

    def test_unparseable_strength_dropped_with_warning(
        self, assembler, population_assembler, timeline_assembler, errors
    ):
        product = self._product(
            assembler,
            population_assembler,
            timeline_assembler,
            [{"name": "S", "strength": "as required"}],
        )
        assert product.ingredients[0].substance.strengths == []
        assert "Could not parse strength" in str(errors.to_dict(Errors.WARNING))

    def test_no_strength_yields_no_strengths(
        self, assembler, population_assembler, timeline_assembler
    ):
        product = self._product(
            assembler, population_assembler, timeline_assembler, [{"name": "S"}]
        )
        assert product.ingredients[0].substance.strengths == []


class TestAdministrationProductLink:
    def test_administration_linked_by_name(
        self, assembler, population_assembler, timeline_assembler
    ):
        a = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            products=[{"name": "Drug A Tablet"}],
            interventions=[
                {
                    "name": "Drug A",
                    "administrations": [
                        {"route": "Oral", "product_name": "Drug A Tablet"}
                    ],
                }
            ],
        )
        product = a.administrable_products[0]
        admin = a.study_interventions[0].administrations[0]
        assert admin.administrableProductId == product.id

    def test_unknown_product_reference_warned_and_null(
        self, assembler, population_assembler, timeline_assembler, errors
    ):
        # Direct assembler use bypasses schema validation; the assembler
        # must guard the reference itself.
        a = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            interventions=[
                {
                    "name": "Drug A",
                    "administrations": [
                        {"route": "Oral", "product_name": "Nonexistent"}
                    ],
                }
            ],
        )
        admin = a.study_interventions[0].administrations[0]
        assert admin.administrableProductId is None
        assert "undeclared product" in str(errors.to_dict(Errors.WARNING))

    def test_no_product_reference_stays_null(
        self, assembler, population_assembler, timeline_assembler
    ):
        a = _execute(
            assembler,
            population_assembler,
            timeline_assembler,
            interventions=[{"name": "Drug A", "administrations": [{"route": "Oral"}]}],
        )
        assert (
            a.study_interventions[0].administrations[0].administrableProductId is None
        )


class TestProductExceptions:
    def _raiser(self, builder, class_name):
        original_create = builder.create

        def maybe_raise(cls, params):
            if cls.__name__ == class_name:
                raise RuntimeError("forced")
            return original_create(cls, params)

        return maybe_raise

    def test_product_creation_exception_logged(
        self, assembler, population_assembler, timeline_assembler, builder
    ):
        with patch.object(
            builder,
            "create",
            side_effect=self._raiser(builder, "AdministrableProduct"),
        ):
            a = _execute(
                assembler,
                population_assembler,
                timeline_assembler,
                products=[{"name": "P"}],
            )
        assert a.administrable_products == []

    def test_ingredient_exception_logged(
        self, assembler, population_assembler, timeline_assembler, builder
    ):
        with patch.object(
            builder, "create", side_effect=self._raiser(builder, "Ingredient")
        ):
            a = _execute(
                assembler,
                population_assembler,
                timeline_assembler,
                products=[{"name": "P", "substances": [{"name": "S"}]}],
            )
        assert a.administrable_products[0].ingredients == []

    def test_substance_none_skipped(
        self, assembler, population_assembler, timeline_assembler, builder
    ):
        original_create = builder.create

        def maybe_none(cls, params):
            if cls.__name__ == "Substance":
                return None
            return original_create(cls, params)

        with patch.object(builder, "create", side_effect=maybe_none):
            a = _execute(
                assembler,
                population_assembler,
                timeline_assembler,
                products=[{"name": "P", "substances": [{"name": "S"}]}],
            )
        assert a.administrable_products[0].ingredients == []
