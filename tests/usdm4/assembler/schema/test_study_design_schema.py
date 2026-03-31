from src.usdm4.assembler.schema.study_design_schema import StudyDesignInput


class TestStudyDesignInput:
    def test_defaults(self):
        sd = StudyDesignInput()
        assert sd.label == ""
        assert sd.trial_phase == ""

    def test_full_input(self):
        data = {"label": "Parallel", "rationale": "Gold standard", "trial_phase": "III"}
        result = StudyDesignInput.model_validate(data)
        assert result.label == "Parallel"
        assert result.trial_phase == "III"
