"""Several study designs in one study version (GitHub 108).

One assembly of a two-design input, shared by the assembly tests (each new
assembly costs a CT and BC load, see ``tests/conftest.py``). The two designs
deliberately repeat names (epochs, visits, activities, arms) to show that
names are unique per design, not across designs. Single-design output is
covered, unchanged, by the existing assembler tests.
"""

import copy
import os
import pathlib

import pytest
from pydantic import ValidationError
from simple_error_log.errors import Errors

from src.usdm4.assembler.assembler import Assembler
from src.usdm4.assembler.schema import AssemblerInput


def root_path():
    base = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


def timeline() -> list[dict]:
    return [
        {
            "type": "main",
            "columns": [
                {
                    "id": "c1",
                    "epoch": {"text": "Screening"},
                    "visit": {"text": "Visit 1"},
                    "timing": {"text": "Day 1", "value": 1, "unit": "days"},
                },
                {
                    "id": "c2",
                    "epoch": {"text": "Treatment"},
                    "visit": {"text": "Visit 2"},
                    "timing": {"text": "Day 7", "value": 7, "unit": "days"},
                },
            ],
            "activities": [
                {"name": "Consent", "cells": [{"column": "c1", "text": "X"}]},
                {"name": "Blood Draw", "cells": [{"column": "c2", "text": "X"}]},
            ],
        }
    ]


def design(
    letter: str, eligibility: dict | None = None, committees: list[str] | None = None
) -> dict:
    result = {
        "study_design": {
            "label": f"Substudy {letter}",
            "rationale": f"Rationale {letter}",
            "trial_phase": "phase-1",
            "arms": [{"name": "Arm 1", "intervention_names": [f"Drug {letter}"]}],
            "interventions": [{"name": f"Drug {letter}"}],
        },
        "soa": timeline(),
        "objectives": {
            "objectives": [
                {
                    "text": f"Objective {letter}",
                    "level": "Primary",
                    "endpoints": [{"text": f"Endpoint {letter}", "level": "Primary"}],
                }
            ]
        },
        "cohorts": [{"name": f"Cohort {letter}", "arm_names": ["Arm 1"]}],
        "planned_enrollment": 20,
    }
    if eligibility is not None:
        result["eligibility"] = eligibility
    if committees is not None:
        result["study_design"]["independent_committees"] = committees
    return result


@pytest.fixture(scope="module")
def two_designs() -> dict:
    return {
        "identification": {
            "titles": {"brief": "Test Study", "official": "Official Test Study"},
            "identifiers": [
                {"identifier": "NCT12345678", "scope": {"standard": "nct"}}
            ],
        },
        "document": {
            "document": {
                "label": "Test Protocol",
                "version": "1.0",
                "status": "final",
                "template": "Protocol Template",
                "version_date": "2024-01-01",
            },
            "sections": [],
        },
        "population": {
            "label": "Test Population",
            "inclusion_exclusion": {
                "inclusion": ["Age >= 18 years"],
                "exclusion": ["Pregnant"],
            },
        },
        "amendments": {
            "identifier": "1",
            "summary": "First amendment",
            "reasons": {"primary": "Change in strategy"},
            "scope": {"global": True},
        },
        "study_designs": [
            design("A", committees=["Independent Data Monitoring Committee"]),
            design("B", {"inclusion": ["Prior vaccination"], "exclusion": []}),
        ],
        "study": {
            "name": {"acronym": "TST"},
            "label": "Test Study",
            "version": "1.0",
            "rationale": "Test study rationale",
        },
    }


@pytest.fixture(scope="module")
def assembled(two_designs):
    errors = Errors()
    assembler = Assembler(root_path(), errors)
    assembler.execute(copy.deepcopy(two_designs))
    return assembler, errors


@pytest.fixture(scope="module")
def version(assembled):
    assembler, _ = assembled
    return assembler.study.versions[0]


class TestTwoDesigns:
    def test_no_errors(self, assembled):
        _, errors = assembled
        assert errors.error_count() == 0, errors.dump(Errors.ERROR)

    def test_two_designs(self, version):
        assert [d.label for d in version.studyDesigns] == ["Substudy A", "Substudy B"]

    def test_own_timelines(self, version):
        a, b = version.studyDesigns
        for d in (a, b):
            assert len(d.scheduleTimelines) == 1
            assert d.scheduleTimelines[0].mainTimeline is True
        assert a.scheduleTimelines[0].id != b.scheduleTimelines[0].id

    def test_own_epochs_same_names(self, version):
        a, b = version.studyDesigns
        assert [e.label for e in a.epochs] == [e.label for e in b.epochs]
        assert not {e.id for e in a.epochs} & {e.id for e in b.epochs}
        for d in (a, b):
            assert d.epochs[0].previousId is None
            assert d.epochs[-1].nextId is None

    def test_own_activities(self, version):
        a, b = version.studyDesigns
        assert [x.label for x in a.activities] == ["Consent", "Blood Draw"]
        assert not {x.id for x in a.activities} & {x.id for x in b.activities}

    def test_own_objectives(self, version):
        a, b = version.studyDesigns
        assert [o.text for o in a.objectives] == ["Objective A"]
        assert [o.text for o in b.objectives] == ["Objective B"]
        assert [e.text for e in b.objectives[0].endpoints] == ["Endpoint B"]

    def test_own_cohorts_wired_to_own_arms(self, version):
        for d, letter in zip(version.studyDesigns, "AB"):
            assert [c.name for c in d.population.cohorts] == [f"COHORT-{letter}"]
            assert d.arms[0].populationIds == [d.population.cohorts[0].id]

    def test_interventions_gathered(self, version):
        names = [i.label for i in version.studyInterventions]
        assert sorted(names) == ["Drug A", "Drug B"]
        a, b = version.studyDesigns
        assert len(a.studyInterventionIds) == 1
        assert a.studyInterventionIds != b.studyInterventionIds

    def test_shared_criteria_held_once(self, version):
        items = version.eligibilityCriterionItems
        assert [i.text for i in items] == [
            "Age >= 18 years",
            "Pregnant",
            "Prior vaccination",
        ]

    def test_criteria_reference_shared_items(self, version):
        a, b = version.studyDesigns
        shared = [c.criterionItemId for c in a.eligibilityCriteria]
        assert len(shared) == 2
        assert set(shared) <= {c.criterionItemId for c in b.eligibilityCriteria}
        assert not {c.id for c in a.eligibilityCriteria} & {
            c.id for c in b.eligibilityCriteria
        }

    def test_design_specific_criterion(self, version):
        a, b = version.studyDesigns
        assert len(b.eligibilityCriteria) == 3
        items = {i.id: i.text for i in version.eligibilityCriterionItems}
        texts = [items[c.criterionItemId] for c in b.eligibilityCriteria]
        assert "Prior vaccination" in texts
        assert "Prior vaccination" not in [
            items[c.criterionItemId] for c in a.eligibilityCriteria
        ]
        assert sorted(b.population.criterionIds) == sorted(
            c.id for c in b.eligibilityCriteria
        )

    def test_design_specific_criterion_chained_after_shared(self, version):
        _, b = version.studyDesigns
        by_id = {c.id: c for c in b.eligibilityCriteria}
        inclusion = [c for c in b.eligibilityCriteria if c.category.code == "C25532"]
        assert len(inclusion) == 2
        assert by_id[inclusion[0].nextId] is inclusion[1]
        assert inclusion[0].previousId is None
        assert inclusion[1].nextId is None

    def test_amendment(self, version):
        assert [a.summary for a in version.amendments] == ["First amendment"]

    def test_design_role_applies_to_its_design(self, version):
        a, _ = version.studyDesigns
        committee = [r for r in version.roles if r.code.code == "C142578"]
        assert len(committee) == 1
        assert committee[0].appliesToIds == [a.id]
        for role in version.roles:
            if role is not committee[0]:
                assert role.appliesToIds == [version.id]


class TestSchema:
    def test_neither_design_form_raises(self, two_designs):
        data = copy.deepcopy(two_designs)
        del data["study_designs"]
        with pytest.raises(ValidationError) as exc_info:
            AssemblerInput.model_validate(data)
        paths = [".".join(str(x) for x in e["loc"]) for e in exc_info.value.errors()]
        assert "study_design" in paths

    @pytest.mark.parametrize(
        "key, value",
        [
            ("study_design", {"label": "Single"}),
            ("soa", []),
            ("objectives", {}),
        ],
    )
    def test_single_design_inputs_with_several_raise(self, two_designs, key, value):
        data = copy.deepcopy(two_designs)
        data[key] = value
        with pytest.raises(ValidationError, match=f"so {key} must not be"):
            AssemblerInput.model_validate(data)

    def test_top_level_cohorts_with_several_raise(self, two_designs):
        data = copy.deepcopy(two_designs)
        data["population"]["cohorts"] = [{"name": "Cohort"}]
        with pytest.raises(ValidationError, match="population.cohorts"):
            AssemblerInput.model_validate(data)

    def test_empty_list_raises(self, two_designs):
        data = copy.deepcopy(two_designs)
        data["study_designs"] = []
        with pytest.raises(ValidationError, match="may not be empty"):
            AssemblerInput.model_validate(data)

    def test_repeated_label_raises(self, two_designs):
        data = copy.deepcopy(two_designs)
        data["study_designs"][1]["study_design"]["label"] = "Substudy A"
        with pytest.raises(ValidationError, match="must be unique"):
            AssemblerInput.model_validate(data)

    def test_missing_label_raises(self, two_designs):
        data = copy.deepcopy(two_designs)
        data["study_designs"][0]["study_design"]["label"] = ""
        with pytest.raises(ValidationError, match="needs a study_design.label"):
            AssemblerInput.model_validate(data)

    def test_cohort_checked_against_own_design(self, two_designs):
        data = copy.deepcopy(two_designs)
        data["study_designs"][1]["study_design"]["arms"][0]["name"] = "Arm 2"
        with pytest.raises(ValidationError, match="undeclared arm 'Arm 1'"):
            AssemblerInput.model_validate(data)

    def test_estimand_checked_against_own_design(self, two_designs):
        data = copy.deepcopy(two_designs)
        objectives = data["study_designs"][1]["objectives"]
        objectives["objectives"][0]["endpoints"][0]["name"] = "EP-B"
        objectives["estimands"] = [
            {
                "summary_measure": "Difference",
                "population_text": "All",
                "endpoint_name": "EP-B",
                "treatment_names": ["Drug A"],
            }
        ]
        with pytest.raises(ValidationError, match="undeclared intervention 'Drug A'"):
            AssemblerInput.model_validate(data)
