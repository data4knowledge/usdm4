import pytest
from uuid import uuid4
from src.usdm4.api.wrapper import Wrapper
from src.usdm4.api.study import Study
from src.usdm4.api.study_version import StudyVersion
from src.usdm4.api.study_design import InterventionalStudyDesign
from src.usdm4.api.code import Code
from src.usdm4.api.study_title import StudyTitle
from src.usdm4.api.identifier import StudyIdentifier
from src.usdm4.api.study_arm import StudyArm
from src.usdm4.api.study_cell import StudyCell
from src.usdm4.api.study_epoch import StudyEpoch
from src.usdm4.api.population_definition import StudyDesignPopulation
from src.usdm4.api.study_definition_document import (
    StudyDefinitionDocument,
    StudyDefinitionDocumentVersion,
)


class TestWrapper:
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.study = Study(
            id=uuid4(),
            name="Test Study",
            description="A test study",
            label="TEST-001",
            versions=[],
            documentedBy=[],
            instanceType="Study",
        )

    def test_basic_initialization(self):
        """Test basic initialization of Wrapper with required fields only."""
        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
        )

        assert wrapper.study == self.study
        assert wrapper.usdmVersion == "3.0"
        assert wrapper.systemName is None
        assert wrapper.systemVersion is None

    def test_initialization_with_all_fields(self):
        """Test initialization of Wrapper with all fields including optional ones."""
        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
            systemName="TestSystem",
            systemVersion="1.2.3",
        )

        assert wrapper.study == self.study
        assert wrapper.usdmVersion == "3.0"
        assert wrapper.systemName == "TestSystem"
        assert wrapper.systemVersion == "1.2.3"

    def test_initialization_with_none_optional_fields(self):
        """Test initialization with explicitly None optional fields."""
        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
            systemName=None,
            systemVersion=None,
        )

        assert wrapper.study == self.study
        assert wrapper.usdmVersion == "3.0"
        assert wrapper.systemName is None
        assert wrapper.systemVersion is None

    def test_initialization_with_partial_optional_fields(self):
        """Test initialization with only some optional fields."""
        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
            systemName="TestSystem",
        )

        assert wrapper.study == self.study
        assert wrapper.usdmVersion == "3.0"
        assert wrapper.systemName == "TestSystem"
        assert wrapper.systemVersion is None

    def test_usdm_version_formats(self):
        """Test various USDM version string formats."""
        versions = ["3.0", "3.0.0", "2.1", "4.0.1-beta"]

        for version in versions:
            wrapper = Wrapper(
                study=self.study,
                usdmVersion=version,
            )
            assert wrapper.usdmVersion == version

    def test_first_version_with_no_versions(self):
        """Test first_version() when study has no versions."""
        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
        )

        result = wrapper.first_version()
        assert result is None

    def test_first_version_with_single_version(self):
        """Test first_version() when study has one version."""
        # Create required codes and objects
        title_type = Code(
            id="title_type1",
            code="OFFICIAL",
            codeSystem="TITLE_TYPE",
            codeSystemVersion="1.0",
            decode="Official Title",
            instanceType="Code",
        )

        study_title = StudyTitle(
            id="title1",
            text="Test Study Title",
            type=title_type,
            instanceType="StudyTitle",
        )

        identifier_type = Code(
            id="id_type1",
            code="SPONSOR",
            codeSystem="ID_TYPE",
            codeSystemVersion="1.0",
            decode="Sponsor Identifier",
            instanceType="Code",
        )

        study_identifier = StudyIdentifier(
            id="identifier1",
            text="STUDY-001",
            type=identifier_type,
            scopeId="org1",
            instanceType="StudyIdentifier",
        )

        # Create a study version
        study_version = StudyVersion(
            id="version1",
            versionIdentifier="1.0",
            rationale="Initial version",
            studyIdentifiers=[study_identifier],
            titles=[study_title],
            instanceType="StudyVersion",
        )

        self.study.versions = [study_version]

        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
        )

        result = wrapper.first_version()
        assert result is not None
        assert result.id == "version1"
        assert result.versionIdentifier == "1.0"

    def test_first_version_with_multiple_versions(self):
        """Test first_version() when study has multiple versions - should return first one."""
        # Create required codes and objects
        title_type = Code(
            id="title_type1",
            code="OFFICIAL",
            codeSystem="TITLE_TYPE",
            codeSystemVersion="1.0",
            decode="Official Title",
            instanceType="Code",
        )

        identifier_type = Code(
            id="id_type1",
            code="SPONSOR",
            codeSystem="ID_TYPE",
            codeSystemVersion="1.0",
            decode="Sponsor Identifier",
            instanceType="Code",
        )

        study_identifier = StudyIdentifier(
            id="identifier1",
            text="STUDY-001",
            type=identifier_type,
            scopeId="org1",
            instanceType="StudyIdentifier",
        )

        # Create multiple study versions
        study_title1 = StudyTitle(
            id="title1",
            text="Test Study Title V1",
            type=title_type,
            instanceType="StudyTitle",
        )

        study_version1 = StudyVersion(
            id="version1",
            versionIdentifier="1.0",
            rationale="Version 1",
            studyIdentifiers=[study_identifier],
            titles=[study_title1],
            instanceType="StudyVersion",
        )

        study_title2 = StudyTitle(
            id="title2",
            text="Test Study Title V2",
            type=title_type,
            instanceType="StudyTitle",
        )

        study_version2 = StudyVersion(
            id="version2",
            versionIdentifier="2.0",
            rationale="Version 2",
            studyIdentifiers=[study_identifier],
            titles=[study_title2],
            instanceType="StudyVersion",
        )

        study_title3 = StudyTitle(
            id="title3",
            text="Test Study Title V3",
            type=title_type,
            instanceType="StudyTitle",
        )

        study_version3 = StudyVersion(
            id="version3",
            versionIdentifier="3.0",
            rationale="Version 3",
            studyIdentifiers=[study_identifier],
            titles=[study_title3],
            instanceType="StudyVersion",
        )

        self.study.versions = [study_version1, study_version2, study_version3]

        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
        )

        result = wrapper.first_version()
        assert result is not None
        assert result.id == "version1"  # Should return the first version
        assert result.versionIdentifier == "1.0"

    def test_wrapper_with_different_studies(self):
        """Test creating wrappers with different study objects."""
        study1 = Study(
            id=uuid4(),
            name="Study 1",
            versions=[],
            documentedBy=[],
            instanceType="Study",
        )

        study2 = Study(
            id=uuid4(),
            name="Study 2",
            versions=[],
            documentedBy=[],
            instanceType="Study",
        )

        wrapper1 = Wrapper(study=study1, usdmVersion="3.0")
        wrapper2 = Wrapper(study=study2, usdmVersion="3.0")

        assert wrapper1.study.name == "Study 1"
        assert wrapper2.study.name == "Study 2"
        assert wrapper1.study != wrapper2.study

    def test_wrapper_immutability(self):
        """Test that wrapper properties can be accessed correctly."""
        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
            systemName="TestSystem",
            systemVersion="1.0.0",
        )

        # Verify all properties are accessible
        assert hasattr(wrapper, "study")
        assert hasattr(wrapper, "usdmVersion")
        assert hasattr(wrapper, "systemName")
        assert hasattr(wrapper, "systemVersion")

    def test_first_version_delegates_to_study(self):
        """Test that first_version() correctly delegates to study.first_version()."""
        # Create required codes and objects
        title_type = Code(
            id="title_type1",
            code="OFFICIAL",
            codeSystem="TITLE_TYPE",
            codeSystemVersion="1.0",
            decode="Official Title",
            instanceType="Code",
        )

        study_title = StudyTitle(
            id="title1",
            text="Test Study Title",
            type=title_type,
            instanceType="StudyTitle",
        )

        identifier_type = Code(
            id="id_type1",
            code="SPONSOR",
            codeSystem="ID_TYPE",
            codeSystemVersion="1.0",
            decode="Sponsor Identifier",
            instanceType="Code",
        )

        study_identifier = StudyIdentifier(
            id="identifier1",
            text="STUDY-001",
            type=identifier_type,
            scopeId="org1",
            instanceType="StudyIdentifier",
        )

        # Create a study version
        study_version = StudyVersion(
            id="version1",
            versionIdentifier="1.0",
            rationale="Initial version",
            studyIdentifiers=[study_identifier],
            titles=[study_title],
            instanceType="StudyVersion",
        )

        self.study.versions = [study_version]

        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
        )

        # Both should return the same result
        wrapper_result = wrapper.first_version()
        study_result = self.study.first_version()

        assert wrapper_result == study_result
        assert wrapper_result.id == study_result.id

    def test_complex_scenario(self):
        """Test a complex scenario with all components."""
        study_id = uuid4()

        # Create required codes and objects
        title_type = Code(
            id="title_type1",
            code="OFFICIAL",
            codeSystem="TITLE_TYPE",
            codeSystemVersion="1.0",
            decode="Official Title",
            instanceType="Code",
        )

        study_title = StudyTitle(
            id="title1",
            text="Complex Test Study",
            type=title_type,
            instanceType="StudyTitle",
        )

        identifier_type = Code(
            id="id_type1",
            code="SPONSOR",
            codeSystem="ID_TYPE",
            codeSystemVersion="1.0",
            decode="Sponsor Identifier",
            instanceType="Code",
        )

        study_identifier = StudyIdentifier(
            id="identifier1",
            text="STUDY-001",
            type=identifier_type,
            scopeId="org1",
            instanceType="StudyIdentifier",
        )

        # Create study version
        study_version = StudyVersion(
            id="version1",
            versionIdentifier="1.0",
            rationale="Complex study initial version",
            studyIdentifiers=[study_identifier],
            titles=[study_title],
            instanceType="StudyVersion",
        )

        # Create study
        study = Study(
            id=study_id,
            name="Complex Study",
            description="A complex test study",
            label="COMPLEX-001",
            versions=[study_version],
            documentedBy=[],
            instanceType="Study",
        )

        # Create wrapper
        wrapper = Wrapper(
            study=study,
            usdmVersion="3.0.1",
            systemName="ProductionSystem",
            systemVersion="2.5.0",
        )

        # Verify all components
        assert wrapper.study.id == study_id
        assert wrapper.study.name == "Complex Study"
        assert wrapper.usdmVersion == "3.0.1"
        assert wrapper.systemName == "ProductionSystem"
        assert wrapper.systemVersion == "2.5.0"

        first_version = wrapper.first_version()
        assert first_version is not None
        assert first_version.versionIdentifier == "1.0"

    def test_multiple_wrappers_same_study(self):
        """Test creating multiple wrappers for the same study object."""
        wrapper1 = Wrapper(
            study=self.study,
            usdmVersion="3.0",
            systemName="System1",
        )

        wrapper2 = Wrapper(
            study=self.study,
            usdmVersion="3.1",
            systemName="System2",
        )

        # Both wrappers reference the same study
        assert wrapper1.study == wrapper2.study
        assert wrapper1.study.name == wrapper2.study.name

        # But have different wrapper properties
        assert wrapper1.usdmVersion != wrapper2.usdmVersion
        assert wrapper1.systemName != wrapper2.systemName

    def test_wrapper_with_empty_study_name(self):
        """Test that wrapper validation works with study validation."""
        # Study requires name to have min_length=1, so empty string should fail
        with pytest.raises(Exception):  # Will be a Pydantic ValidationError
            study = Study(
                id=uuid4(),
                name="",  # Empty string should fail validation
                versions=[],
                documentedBy=[],
                instanceType="Study",
            )
            Wrapper(
                study=study,
                usdmVersion="3.0",
            )

    def test_wrapper_serialization_structure(self):
        """Test that wrapper can be serialized to dict."""
        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
            systemName="TestSystem",
            systemVersion="1.0.0",
        )

        wrapper_dict = wrapper.model_dump()

        assert "study" in wrapper_dict
        assert "usdmVersion" in wrapper_dict
        assert "systemName" in wrapper_dict
        assert "systemVersion" in wrapper_dict

        assert wrapper_dict["usdmVersion"] == "3.0"
        assert wrapper_dict["systemName"] == "TestSystem"
        assert wrapper_dict["systemVersion"] == "1.0.0"

    # =====================================================
    # Tests for study_version_and_design method
    # =====================================================

    def _create_study_version_with_design(self, version_id: str, design_id: str = None):
        """Helper method to create a StudyVersion with optional StudyDesign."""
        title_type = Code(
            id="title_type1",
            code="OFFICIAL",
            codeSystem="TITLE_TYPE",
            codeSystemVersion="1.0",
            decode="Official Title",
            instanceType="Code",
        )

        study_title = StudyTitle(
            id="title1",
            text="Test Study Title",
            type=title_type,
            instanceType="StudyTitle",
        )

        identifier_type = Code(
            id="id_type1",
            code="SPONSOR",
            codeSystem="ID_TYPE",
            codeSystemVersion="1.0",
            decode="Sponsor Identifier",
            instanceType="Code",
        )

        study_identifier = StudyIdentifier(
            id="identifier1",
            text="STUDY-001",
            type=identifier_type,
            scopeId="org1",
            instanceType="StudyIdentifier",
        )

        study_designs = []
        if design_id:
            study_designs.append(self._create_study_design(design_id))

        return StudyVersion(
            id=version_id,
            versionIdentifier="1.0",
            rationale="Test version",
            studyIdentifiers=[study_identifier],
            titles=[study_title],
            studyDesigns=study_designs,
            instanceType="StudyVersion",
        )

    def _create_study_design(self, design_id: str, name: str = "Test Design"):
        """Helper method to create an InterventionalStudyDesign."""
        model_code = Code(
            id="model_code1",
            code="C82639",
            codeSystem="http://www.cdisc.org",
            codeSystemVersion="2024-09-27",
            decode="Parallel Study",
            instanceType="Code",
        )

        arm_type = Code(
            id="arm_type1",
            code="C174265",
            codeSystem="http://www.cdisc.org",
            codeSystemVersion="2024-09-27",
            decode="Treatment Arm",
            instanceType="Code",
        )

        epoch_type = Code(
            id="epoch_type1",
            code="C98779",
            codeSystem="http://www.cdisc.org",
            codeSystemVersion="2024-09-27",
            decode="Treatment Period",
            instanceType="Code",
        )

        data_origin_type = Code(
            id="data_origin_type1",
            code="C25301",
            codeSystem="http://www.cdisc.org",
            codeSystemVersion="2024-09-27",
            decode="Collected",
            instanceType="Code",
        )

        study_arm = StudyArm(
            id="arm1",
            name="Treatment Arm",
            description="Test treatment arm",
            label="ARM-1",
            type=arm_type,
            dataOriginDescription="Data collected from test subjects",
            dataOriginType=data_origin_type,
            instanceType="StudyArm",
        )

        study_epoch = StudyEpoch(
            id="epoch1",
            name="Treatment Epoch",
            description="Test epoch",
            label="EPOCH-1",
            type=epoch_type,
            instanceType="StudyEpoch",
        )

        study_cell = StudyCell(
            id="cell1",
            armId="arm1",
            epochId="epoch1",
            elementIds=[],
            instanceType="StudyCell",
        )

        population = StudyDesignPopulation(
            id="pop1",
            name="Test Population",
            description="Test population description",
            label="POP-1",
            includesHealthySubjects=True,
            instanceType="StudyDesignPopulation",
        )

        return InterventionalStudyDesign(
            id=design_id,
            name=name,
            description="Test study design",
            label="DESIGN-1",
            rationale="Test rationale",
            arms=[study_arm],
            epochs=[study_epoch],
            studyCells=[study_cell],
            population=population,
            model=model_code,
            instanceType="InterventionalStudyDesign",
        )

    def test_study_version_and_design_no_versions(self):
        """Test study_version_and_design() when study has no versions."""
        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
        )

        study, version, design = wrapper.study_version_and_design("some_design_id")

        assert study is None
        assert version is None
        assert design is None

    def test_study_version_and_design_version_without_designs(self):
        """Test study_version_and_design() when study has version but no study designs."""
        study_version = self._create_study_version_with_design(
            "version1", design_id=None
        )
        self.study.versions = [study_version]

        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
        )

        study, version, design = wrapper.study_version_and_design("some_design_id")

        assert study is not None
        assert study == self.study
        assert version is not None
        assert version.id == "version1"
        assert design is None

    def test_study_version_and_design_design_id_not_found(self):
        """Test study_version_and_design() when design id doesn't match any study design."""
        study_version = self._create_study_version_with_design(
            "version1", design_id="design1"
        )
        self.study.versions = [study_version]

        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
        )

        study, version, design = wrapper.study_version_and_design(
            "non_existent_design_id"
        )

        assert study is not None
        assert study == self.study
        assert version is not None
        assert version.id == "version1"
        assert design is None

    def test_study_version_and_design_design_found(self):
        """Test study_version_and_design() when design id matches a study design."""
        study_version = self._create_study_version_with_design(
            "version1", design_id="design1"
        )
        self.study.versions = [study_version]

        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
        )

        study, version, design = wrapper.study_version_and_design("design1")

        assert study is not None
        assert study == self.study
        assert version is not None
        assert version.id == "version1"
        assert design is not None
        assert design.id == "design1"

    def test_study_version_and_design_multiple_designs_find_first(self):
        """Test study_version_and_design() finds correct design from multiple designs."""
        title_type = Code(
            id="title_type1",
            code="OFFICIAL",
            codeSystem="TITLE_TYPE",
            codeSystemVersion="1.0",
            decode="Official Title",
            instanceType="Code",
        )

        study_title = StudyTitle(
            id="title1",
            text="Test Study Title",
            type=title_type,
            instanceType="StudyTitle",
        )

        identifier_type = Code(
            id="id_type1",
            code="SPONSOR",
            codeSystem="ID_TYPE",
            codeSystemVersion="1.0",
            decode="Sponsor Identifier",
            instanceType="Code",
        )

        study_identifier = StudyIdentifier(
            id="identifier1",
            text="STUDY-001",
            type=identifier_type,
            scopeId="org1",
            instanceType="StudyIdentifier",
        )

        design1 = self._create_study_design("design1", name="Design 1")
        design2 = self._create_study_design("design2", name="Design 2")
        design3 = self._create_study_design("design3", name="Design 3")

        study_version = StudyVersion(
            id="version1",
            versionIdentifier="1.0",
            rationale="Test version",
            studyIdentifiers=[study_identifier],
            titles=[study_title],
            studyDesigns=[design1, design2, design3],
            instanceType="StudyVersion",
        )

        self.study.versions = [study_version]

        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
        )

        # Find first design
        study, version, design = wrapper.study_version_and_design("design1")
        assert study is not None
        assert version is not None
        assert design is not None
        assert design.id == "design1"
        assert design.name == "Design 1"

    def test_study_version_and_design_multiple_designs_find_middle(self):
        """Test study_version_and_design() finds correct design from the middle of multiple designs."""
        title_type = Code(
            id="title_type1",
            code="OFFICIAL",
            codeSystem="TITLE_TYPE",
            codeSystemVersion="1.0",
            decode="Official Title",
            instanceType="Code",
        )

        study_title = StudyTitle(
            id="title1",
            text="Test Study Title",
            type=title_type,
            instanceType="StudyTitle",
        )

        identifier_type = Code(
            id="id_type1",
            code="SPONSOR",
            codeSystem="ID_TYPE",
            codeSystemVersion="1.0",
            decode="Sponsor Identifier",
            instanceType="Code",
        )

        study_identifier = StudyIdentifier(
            id="identifier1",
            text="STUDY-001",
            type=identifier_type,
            scopeId="org1",
            instanceType="StudyIdentifier",
        )

        design1 = self._create_study_design("design1", name="Design 1")
        design2 = self._create_study_design("design2", name="Design 2")
        design3 = self._create_study_design("design3", name="Design 3")

        study_version = StudyVersion(
            id="version1",
            versionIdentifier="1.0",
            rationale="Test version",
            studyIdentifiers=[study_identifier],
            titles=[study_title],
            studyDesigns=[design1, design2, design3],
            instanceType="StudyVersion",
        )

        self.study.versions = [study_version]

        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
        )

        # Find middle design
        study, version, design = wrapper.study_version_and_design("design2")
        assert study is not None
        assert version is not None
        assert design is not None
        assert design.id == "design2"
        assert design.name == "Design 2"

    def test_study_version_and_design_multiple_designs_find_last(self):
        """Test study_version_and_design() finds correct design from the end of multiple designs."""
        title_type = Code(
            id="title_type1",
            code="OFFICIAL",
            codeSystem="TITLE_TYPE",
            codeSystemVersion="1.0",
            decode="Official Title",
            instanceType="Code",
        )

        study_title = StudyTitle(
            id="title1",
            text="Test Study Title",
            type=title_type,
            instanceType="StudyTitle",
        )

        identifier_type = Code(
            id="id_type1",
            code="SPONSOR",
            codeSystem="ID_TYPE",
            codeSystemVersion="1.0",
            decode="Sponsor Identifier",
            instanceType="Code",
        )

        study_identifier = StudyIdentifier(
            id="identifier1",
            text="STUDY-001",
            type=identifier_type,
            scopeId="org1",
            instanceType="StudyIdentifier",
        )

        design1 = self._create_study_design("design1", name="Design 1")
        design2 = self._create_study_design("design2", name="Design 2")
        design3 = self._create_study_design("design3", name="Design 3")

        study_version = StudyVersion(
            id="version1",
            versionIdentifier="1.0",
            rationale="Test version",
            studyIdentifiers=[study_identifier],
            titles=[study_title],
            studyDesigns=[design1, design2, design3],
            instanceType="StudyVersion",
        )

        self.study.versions = [study_version]

        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
        )

        # Find last design
        study, version, design = wrapper.study_version_and_design("design3")
        assert study is not None
        assert version is not None
        assert design is not None
        assert design.id == "design3"
        assert design.name == "Design 3"

    def test_study_version_and_design_uses_first_version_only(self):
        """Test study_version_and_design() only uses the first version even with multiple versions."""
        title_type = Code(
            id="title_type1",
            code="OFFICIAL",
            codeSystem="TITLE_TYPE",
            codeSystemVersion="1.0",
            decode="Official Title",
            instanceType="Code",
        )

        identifier_type = Code(
            id="id_type1",
            code="SPONSOR",
            codeSystem="ID_TYPE",
            codeSystemVersion="1.0",
            decode="Sponsor Identifier",
            instanceType="Code",
        )

        study_identifier = StudyIdentifier(
            id="identifier1",
            text="STUDY-001",
            type=identifier_type,
            scopeId="org1",
            instanceType="StudyIdentifier",
        )

        # First version has design1
        design1 = self._create_study_design("design1", name="Design from V1")
        study_title1 = StudyTitle(
            id="title1",
            text="Test Study Title V1",
            type=title_type,
            instanceType="StudyTitle",
        )
        version1 = StudyVersion(
            id="version1",
            versionIdentifier="1.0",
            rationale="Version 1",
            studyIdentifiers=[study_identifier],
            titles=[study_title1],
            studyDesigns=[design1],
            instanceType="StudyVersion",
        )

        # Second version has design2 (which should NOT be findable)
        design2 = self._create_study_design("design2", name="Design from V2")
        study_title2 = StudyTitle(
            id="title2",
            text="Test Study Title V2",
            type=title_type,
            instanceType="StudyTitle",
        )
        version2 = StudyVersion(
            id="version2",
            versionIdentifier="2.0",
            rationale="Version 2",
            studyIdentifiers=[study_identifier],
            titles=[study_title2],
            studyDesigns=[design2],
            instanceType="StudyVersion",
        )

        self.study.versions = [version1, version2]

        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
        )

        # Design from first version should be found
        study, version, design = wrapper.study_version_and_design("design1")
        assert study is not None
        assert study == self.study
        assert version is not None
        assert version.id == "version1"
        assert design is not None
        assert design.id == "design1"

        # Design from second version should NOT be found
        study, version, design = wrapper.study_version_and_design("design2")
        assert study is not None
        assert study == self.study
        assert version is not None
        assert version.id == "version1"  # Still returns first version
        assert design is None  # But design2 is not in first version

    def test_study_version_and_design_empty_id(self):
        """Test study_version_and_design() with empty string id."""
        study_version = self._create_study_version_with_design(
            "version1", design_id="design1"
        )
        self.study.versions = [study_version]

        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
        )

        study, version, design = wrapper.study_version_and_design("")

        assert study is not None
        assert study == self.study
        assert version is not None
        assert version.id == "version1"
        assert design is None

    def test_study_version_and_design_returns_correct_types(self):
        """Test study_version_and_design() returns correct tuple types."""
        study_version = self._create_study_version_with_design(
            "version1", design_id="design1"
        )
        self.study.versions = [study_version]

        wrapper = Wrapper(
            study=self.study,
            usdmVersion="3.0",
        )

        result = wrapper.study_version_and_design("design1")

        assert isinstance(result, tuple)
        assert len(result) == 3
        assert isinstance(result[0], Study)
        assert isinstance(result[1], StudyVersion)
        assert isinstance(result[2], InterventionalStudyDesign)

    # =====================================================
    # Tests for study_document_version method
    # =====================================================

    def _create_document_version(
        self, version_id: str
    ) -> StudyDefinitionDocumentVersion:
        """Helper to create a StudyDefinitionDocumentVersion."""
        status_code = Code(
            id="status_code1",
            code="C99079x2",
            codeSystem="http://www.cdisc.org",
            codeSystemVersion="2024-09-27",
            decode="Final",
            instanceType="Code",
        )
        return StudyDefinitionDocumentVersion(
            id=version_id,
            version="1.0",
            status=status_code,
            instanceType="StudyDefinitionDocumentVersion",
        )

    def _create_document(
        self, template_name: str, doc_versions: list[StudyDefinitionDocumentVersion]
    ) -> StudyDefinitionDocument:
        """Helper to create a StudyDefinitionDocument."""
        language_code = Code(
            id="lang_code1",
            code="en",
            codeSystem="ISO 639-1",
            codeSystemVersion="2024",
            decode="English",
            instanceType="Code",
        )
        type_code = Code(
            id="doc_type_code1",
            code="C70817",
            codeSystem="http://www.cdisc.org",
            codeSystemVersion="2024-09-27",
            decode="Protocol",
            instanceType="Code",
        )
        return StudyDefinitionDocument(
            id=f"doc_{template_name}",
            name=f"Document {template_name}",
            templateName=template_name,
            language=language_code,
            type=type_code,
            versions=doc_versions,
            instanceType="StudyDefinitionDocument",
        )

    def _create_wrapper_with_documents(
        self,
        documents: list[StudyDefinitionDocument],
        document_version_ids: list[str],
    ) -> Wrapper:
        """Helper to create a Wrapper with a study version linked to documents."""
        study_version = self._create_study_version_with_design("version1")
        study_version.documentVersionIds = document_version_ids
        self.study.versions = [study_version]
        self.study.documentedBy = documents
        return Wrapper(study=self.study, usdmVersion="3.0")

    def test_study_document_version_no_versions(self):
        """Test study_document_version() returns None when study has no versions."""
        wrapper = Wrapper(study=self.study, usdmVersion="3.0")
        result = wrapper.study_document_version("protocol")
        assert result is None

    def test_study_document_version_no_documents(self):
        """Test study_document_version() returns None when version has no documents."""
        study_version = self._create_study_version_with_design("version1")
        self.study.versions = [study_version]
        wrapper = Wrapper(study=self.study, usdmVersion="3.0")
        result = wrapper.study_document_version("protocol")
        assert result is None

    def test_study_document_version_template_not_found(self):
        """Test study_document_version() returns None when template name doesn't match."""
        doc_version = self._create_document_version("dv1")
        doc = self._create_document("protocol", [doc_version])
        wrapper = self._create_wrapper_with_documents([doc], ["dv1"])
        result = wrapper.study_document_version("nonexistent")
        assert result is None

    def test_study_document_version_found(self):
        """Test study_document_version() returns the correct document version."""
        doc_version = self._create_document_version("dv1")
        doc = self._create_document("protocol", [doc_version])
        wrapper = self._create_wrapper_with_documents([doc], ["dv1"])
        result = wrapper.study_document_version("protocol")
        assert result is not None
        assert isinstance(result, StudyDefinitionDocumentVersion)
        assert result.id == "dv1"

    def test_study_document_version_case_insensitive(self):
        """Test study_document_version() matches template name case-insensitively."""
        doc_version = self._create_document_version("dv1")
        doc = self._create_document("Protocol", [doc_version])
        wrapper = self._create_wrapper_with_documents([doc], ["dv1"])

        assert wrapper.study_document_version("protocol") is not None
        assert wrapper.study_document_version("PROTOCOL") is not None
        assert wrapper.study_document_version("Protocol") is not None

    def test_study_document_version_multiple_documents(self):
        """Test study_document_version() finds the correct document among multiple."""
        dv1 = self._create_document_version("dv1")
        dv2 = self._create_document_version("dv2")
        doc1 = self._create_document("protocol", [dv1])
        doc2 = self._create_document("icf", [dv2])
        wrapper = self._create_wrapper_with_documents([doc1, doc2], ["dv1", "dv2"])

        result = wrapper.study_document_version("icf")
        assert result is not None
        assert result.id == "dv2"

        result = wrapper.study_document_version("protocol")
        assert result is not None
        assert result.id == "dv1"
