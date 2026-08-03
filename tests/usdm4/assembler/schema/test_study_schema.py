from src.usdm4.assembler.schema.study_schema import StudyInput, StudyName


class TestStudyName:
    def test_defaults(self):
        n = StudyName()
        assert n.identifier == ""
        assert n.acronym == ""
        assert n.compound == ""

    def test_partial(self):
        n = StudyName.model_validate({"acronym": "TST"})
        assert n.acronym == "TST"
        assert n.identifier == ""


class TestStudyInput:
    def test_defaults(self):
        s = StudyInput()
        assert s.version == ""
        assert s.original_protocol == ""

    def test_full_input(self):
        data = {
            "name": {"identifier": "STUDY-001", "acronym": "S1"},
            "label": "Study One",
            "version": "2.0",
            "rationale": "Updated",
            "sponsor_approval_date": "2024-03-15",
            "confidentiality": "Confidential",
            "original_protocol": "Yes",
        }
        result = StudyInput.model_validate(data)
        assert result.name.identifier == "STUDY-001"
        assert result.version == "2.0"
        assert result.original_protocol == "Yes"
