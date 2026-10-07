"""M11 1.1.2 (Overall Design) inputs on the study design assembler (issue 83).

Each field goes from assembler input to the USDM path DDF-RA's
m11_mapping.xlsx names (and the usdm4_protocol 1.1.2 view reads).
"""

import copy
import os
import pathlib
import pytest
from simple_error_log.errors import Errors
from src.usdm4.assembler.assembler import Assembler
from src.usdm4.assembler.encoder import Encoder
from src.usdm4.builder.builder import Builder


def root_path():
    base = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


BASE = {
    "identification": {
        "titles": {"brief": "Test Study", "official": "Official Test Study"},
        "identifiers": [{"identifier": "NCT12345678", "scope": {"standard": "nct"}}],
    },
    "document": {
        "document": {
            "label": "Test Protocol",
            "version": "1.0",
            "status": "final",
            "template": "M11",
            "version_date": "2024-01-01",
        },
        "sections": [],
    },
    "population": {"label": "Test Population"},
    "study_design": {
        "label": "Test Study Design",
        "rationale": "Test rationale",
        "trial_phase": "phase-2",
    },
    "study": {
        "name": {"acronym": "TST"},
        "label": "Test Study",
        "version": "1.0",
        "rationale": "Test study rationale",
    },
}

SOA = [
    {
        "type": "main",
        "columns": [
            {
                "id": "c1",
                "epoch": {"text": "Screening"},
                "visit": {"text": "Visit 1"},
                "timing": {"text": "Day 1", "value": 1, "unit": "days"},
                "window": {"before": 0, "after": 0, "unit": "days"},
            },
        ],
        "activities": [{"name": "Consent", "cells": [{"column": "c1", "text": "X"}]}],
    }
]


SPONSOR_IDENTIFIER = {
    "identifier": "SPONSOR-001",
    "scope": {
        "non_standard": {
            "type": "pharma",
            "role": "sponsor",
            "name": "Test Pharma",
            "label": "Test Pharma",
            "identifier": "TP",
            "identifierScheme": "DUNS",
            "legalAddress": {
                "lines": ["1 Main St"],
                "city": "Copenhagen",
                "district": "",
                "state": "",
                "postalCode": "1000",
                "country": "DNK",
            },
        }
    },
}


def assemble(design: dict, soa: list | None = None, sponsor: bool = False):
    errors = Errors()
    assembler = Assembler(root_path(), errors)
    data = copy.deepcopy(BASE)
    if sponsor:
        data["identification"]["identifiers"].append(copy.deepcopy(SPONSOR_IDENTIFIER))
    data["study_design"].update(design)
    if soa is not None:
        data["soa"] = copy.deepcopy(soa)
    assembler.execute(data)
    assert assembler.study is not None, errors.dump(0)
    version = assembler.study.versions[0]
    return version, version.studyDesigns[0], errors


def codes(items) -> list[str]:
    return [c.code for c in items]


class TestIndications:
    def test_one_indication_per_condition(self):
        _, design, _ = assemble({"indications": ["Type 3 VWD", " Thrombosis "]})
        assert [i.label for i in design.indications] == ["Type 3 VWD", "Thrombosis"]
        assert all(i.isRareDisease is False for i in design.indications)

    def test_blank_entries_dropped(self):
        _, design, _ = assemble({"indications": ["", "  "]})
        assert design.indications == []

    def test_none_stated(self):
        _, design, _ = assemble({})
        assert design.indications == []


class TestCharacteristics:
    def test_site_distribution(self):
        _, design, _ = assemble({"site_distribution": "Multicentre"})
        assert codes(design.characteristics) == ["C217005"]
        _, design, _ = assemble({"site_distribution": "Single-Centre"})
        assert codes(design.characteristics) == ["C217004"]

    def test_site_geographic_scope(self):
        _, design, _ = assemble({"site_geographic_scope": "Multiple Countries"})
        assert codes(design.characteristics) == ["C217007"]
        _, design, _ = assemble({"site_geographic_scope": "single country"})
        assert codes(design.characteristics) == ["C217006"]

    def test_assignment_randomisation(self):
        _, design, _ = assemble({"intervention_assignment_method": "Randomisation"})
        assert codes(design.characteristics) == ["C46079"]

    def test_assignment_stratified(self):
        _, design, _ = assemble(
            {"intervention_assignment_method": "Stratified Randomization"}
        )
        assert codes(design.characteristics) == ["C147145"]

    def test_assignment_without_usdm_home(self):
        _, design, _ = assemble(
            {"intervention_assignment_method": "No Intervention Assignment Method"}
        )
        assert design.characteristics == []

    def test_all_three(self):
        _, design, _ = assemble(
            {
                "site_distribution": "Multicentre",
                "site_geographic_scope": "Multiple Countries",
                "intervention_assignment_method": "Randomisation",
            }
        )
        assert codes(design.characteristics) == ["C217005", "C217007", "C46079"]

    def test_unknown_value_not_defaulted(self):
        _, design, errors = assemble({"site_distribution": "Approximately 25 centers"})
        assert design.characteristics == []
        assert "not decoded" in str(errors.dump(0))


class TestBlindingSchema:
    @pytest.mark.parametrize(
        "text, code",
        [
            ("Double Blind", "C15228"),
            ("double-blind", "C15228"),
            ("Open Label", "C49659"),
            ("Open-label.", "C49659"),
            ("Single Blind", "C28233"),
            ("Observer Blind", "C187674"),
        ],
    )
    def test_decoded(self, text, code):
        _, design, _ = assemble({"blinding_schema": text})
        assert design.blindingSchema.standardCode.code == code

    @pytest.mark.parametrize("text", [None, "", "Not applicable", "N/A"])
    def test_not_stated(self, text):
        _, design, _ = assemble({"blinding_schema": text})
        assert design.blindingSchema is None


class TestRoles:
    def test_blinded_roles_masked(self):
        version, _, _ = assemble({"blinded_roles": ["Participant", "Investigator"]})
        masked = [r for r in version.roles if r.masking and r.masking.isMasked]
        assert sorted(r.code.code for r in masked) == ["C25936", "C41189"]
        assert all(r.appliesToIds == [version.id] for r in masked)

    def test_blinded_sponsor_reuses_sponsor_role(self):
        version, _, _ = assemble({"blinded_roles": ["Sponsor"]}, sponsor=True)
        sponsors = [r for r in version.roles if r.code.code == "C70793"]
        assert len(sponsors) == 1
        assert sponsors[0].masking.isMasked is True
        assert sponsors[0].organizationIds

    def test_blinded_sponsor_without_sponsor_role_dropped(self):
        version, _, errors = assemble({"blinded_roles": ["Sponsor"]})
        assert not [r for r in version.roles if r.code.code == "C70793"]
        assert "no sponsor role to mask" in str(errors.dump(0))

    def test_blinded_not_applicable(self):
        version, _, _ = assemble({"blinded_roles": ["Not Applicable"]})
        assert not [r for r in version.roles if r.masking]

    def test_independent_committees(self):
        version, _, _ = assemble(
            {
                "independent_committees": [
                    "Independent Data Monitoring Committee",
                    "Endpoint Adjudication Committee",
                ]
            }
        )
        found = {r.code.code: r.label for r in version.roles}
        assert found["C142578"] == "Independent Data Monitoring Committee"
        assert found["C78726"] == "Endpoint Adjudication Committee"

    def test_unknown_independent_committee_dropped(self):
        version, _, errors = assemble({"independent_committees": ["Steering Committee"]})
        assert not [r for r in version.roles if r.label == "Steering Committee"]
        assert "not decoded" in str(errors.dump(0))

    def test_other_committees(self):
        version, _, _ = assemble(
            {"other_committees": ["Executive Oversight Committee", "N/A"]}
        )
        other = [r for r in version.roles if r.code.code == "C142489"]
        assert [r.label for r in other] == ["Executive Oversight Committee"]
        assert other[0].appliesToIds == [version.id]

    def test_role_names_unique(self):
        version, _, _ = assemble(
            {
                "blinded_roles": ["Participant"],
                "independent_committees": ["IDMC"],
                "other_committees": ["Steering Committee"],
            }
        )
        names = [r.name for r in version.roles]
        assert len(names) == len(set(names))


class TestParticipationDuration:
    def test_quantity_on_main_timeline(self):
        _, design, _ = assemble(
            {"participation_duration": {"quantity": "26 weeks"}}, soa=SOA
        )
        duration = design.main_timeline().plannedDuration
        assert duration.quantity.value == 26
        assert duration.durationWillVary is False

    def test_will_vary_reason(self):
        reason = "Duration will vary by participant based on continued benefit"
        _, design, _ = assemble(
            {"participation_duration": {"will_vary": True, "will_vary_reason": reason}},
            soa=SOA,
        )
        duration = design.main_timeline().plannedDuration
        assert duration.durationWillVary is True
        assert duration.reasonDurationWillVary == reason

    def test_no_timeline_warns(self):
        _, design, errors = assemble({"participation_duration": {"quantity": "26 weeks"}})
        assert design.scheduleTimelines == []
        assert "no main timeline" in str(errors.dump(0))

    def test_not_stated(self):
        _, design, _ = assemble({}, soa=SOA)
        assert design.main_timeline().plannedDuration is None


@pytest.fixture(scope="module")
def encoder():
    return Encoder(Builder(root_path(), Errors()), Errors())


class TestEncoderNormalisation:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Double-blind.", "DOUBLE BLIND"),
            ("  open_label ", "OPEN LABEL"),
            ("Multi  Centre", "MULTI CENTRE"),
            (None, ""),
        ],
    )
    def test_normalise_label(self, encoder, text, expected):
        assert encoder._normalise_label(text) == expected

    def test_blinded_role_participant_is_study_subject(self, encoder):
        assert encoder.blinded_role("Participant").code == "C41189"

    def test_care_provider(self, encoder):
        assert encoder.blinded_role("Care Provider").code == "C17445"
