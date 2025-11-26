import pytest
from uuid import uuid4
from src.usdm4.api.wrapper import Wrapper
from src.usdm4.api.study import Study
from src.usdm4.api.study_version import StudyVersion
from src.usdm4.api.code import Code
from src.usdm4.api.study_title import StudyTitle
from src.usdm4.api.identifier import StudyIdentifier

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
        assert hasattr(wrapper, 'study')
        assert hasattr(wrapper, 'usdmVersion')
        assert hasattr(wrapper, 'systemName')
        assert hasattr(wrapper, 'systemVersion')

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
