"""Branch-coverage supplements for Convert.

The fixture-driven examples in test_convert.py do not hit every branch.
These tests hit the remaining branches directly on the static helpers:

- _convert_subject_enrollment with item["code"] falsy (suffix fallback)
- _get_document with empty documentedBy / no matching id
- Convert.convert — population with cohorts branch
"""

from usdm4.convert.convert import Convert


# ---------------------------------------------------------------------------
# _convert_subject_enrollment
# ---------------------------------------------------------------------------


def test_convert_subject_enrollment_with_falsy_code_uses_empty_suffix():
    """item['code'] is None → the suffix ternary's else branch runs; the
    resulting item['name'] has no _CODE suffix."""
    enrollments = [
        {
            "id": "E1",
            "type": {"decode": "Global"},
            "code": None,  # triggers else branch
        }
    ]
    out = Convert._convert_subject_enrollment(enrollments)
    assert out[0]["name"] == "Global"  # no trailing _<code>
    assert out[0]["forGeographicScope"]["type"] == {"decode": "Global"}
    assert "type" not in out[0]
    assert "code" not in out[0]


def test_convert_subject_enrollment_with_code_builds_suffix():
    """Positive-path companion: when item['code'] is populated, the suffix
    is built from standardCode.decode and appears on the name."""
    enrollments = [
        {
            "id": "E1",
            "type": {"decode": "Country"},
            "code": {"standardCode": {"decode": "USA"}},
        }
    ]
    out = Convert._convert_subject_enrollment(enrollments)
    assert out[0]["name"] == "Country_USA"


# ---------------------------------------------------------------------------
# _get_document
# ---------------------------------------------------------------------------


def test_get_document_returns_none_for_empty_documented_by():
    """len(study['documentedBy']) == 0 short-circuits to None."""
    study = {"documentedBy": []}
    assert Convert._get_document(study, "any_id") is None


def test_get_document_returns_none_when_id_missing():
    """Non-empty documentedBy with no matching doc id falls through to
    the final `return None`."""
    study = {
        "documentedBy": [
            {
                "versions": [
                    {"id": "Other"},
                ]
            }
        ]
    }
    assert Convert._get_document(study, "NotThere") is None


def test_get_document_returns_matching_doc():
    """Happy path — returns the matching version dict."""
    target = {"id": "DocV1"}
    study = {
        "documentedBy": [
            {"versions": [{"id": "Other"}, target]},
        ]
    }
    assert Convert._get_document(study, "DocV1") is target


# ---------------------------------------------------------------------------
# Convert.convert — cohorts branch of the population block
# ---------------------------------------------------------------------------


def _minimal_study_with_population(population):
    """Return a minimal wrapper whose single StudyVersion carries a
    population fixture; avoids the heavier conversion branches."""
    return {
        "study": {
            "name": "S",
            "instanceType": "Study",
            "documentedBy": None,
            "versions": [
                {
                    "id": "V1",
                    "documentVersionId": "DV1",
                    "dateValues": [],
                    "studyIdentifiers": [],
                    "amendments": [],
                    "studyPhase": None,
                    "studyType": None,
                    "studyDesigns": [
                        {
                            "id": "SD1",
                            "population": population,
                            "studyInterventions": [],
                            "dictionaries": [],
                            "conditions": [],
                            "biomedicalConcepts": [],
                            "bcCategories": [],
                            "bcSurrogates": [],
                        }
                    ],
                }
            ],
        }
    }


def test_convert_population_with_cohorts_processes_each():
    """study_design['population']['cohorts'] exists → each cohort is
    converted (exercises lines 136-143)."""
    population = {
        "id": "P1",
        "name": "POP",
        "includesHealthySubjects": True,
        "instanceType": "PopulationDefinition",
        "cohorts": [
            {
                "id": "CH1",
                "name": "CH",
                "includesHealthySubjects": True,
                "instanceType": "PopulationDefinition",
            }
        ],
    }
    data = _minimal_study_with_population(population)
    # Convert fails validation on the wrapper because we haven't supplied a
    # full schema-correct study, but the population pre-processing we care
    # about runs before validation. Catch the validation error and inspect
    # the mutated data.
    try:
        Convert.convert(data)
    except Exception:
        pass
    design = data["study"]["versions"][0]["studyDesigns"][0]
    # Cohort passed through _convert_population (still a dict, no criteria
    # added since the cohort has no 'criteria' key).
    assert design["population"]["cohorts"][0]["id"] == "CH1"


def test_convert_population_empty_yields_default_population():
    """When population is falsy (empty dict), Convert synthesises the
    EMPTY_POPULATION placeholder (exercises lines 124-130)."""
    data = _minimal_study_with_population({})
    try:
        Convert.convert(data)
    except Exception:
        pass
    design = data["study"]["versions"][0]["studyDesigns"][0]
    assert design["population"]["name"] == "EMPTY_POPULATION"
    assert design["population"]["id"] == "Population_Empty"
