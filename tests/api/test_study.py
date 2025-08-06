import pytest
from uuid import uuid4, UUID
from src.usdm4.api.study import Study
from src.usdm4.api.study_version import StudyVersion
from src.usdm4.api.study_definition_document import StudyDefinitionDocument
from src.usdm4.api.code import Code


class TestStudy:
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.study_id = uuid4()
        self.study = Study(
            id=self.study_id,
            name="Test Study",
            description="A test study for validation",
            label="TEST-001",
            instanceType="Study"
        )

    def test_basic_initialization(self):
        """Test basic initialization of Study."""
        assert self.study.id == self.study_id
        assert self.study.name == "Test Study"
        assert self.study.description == "A test study for validation"
        assert self.study.label == "TEST-001"
        assert self.study.versions == []
        assert self.study.documentedBy == []
        assert self.study.instanceType == "Study"

    def test_initialization_with_minimal_fields(self):
        """Test initialization with only required fields."""
        minimal_study = Study(
            name="Minimal Study",
            instanceType="Study"
        )
        
        assert minimal_study.id is None
        assert minimal_study.name == "Minimal Study"
        assert minimal_study.description is None
        assert minimal_study.label is None
        assert minimal_study.versions == []
        assert minimal_study.documentedBy == []
        assert minimal_study.instanceType == "Study"

    def test_name_validation(self):
        """Test that name field validation works (min_length=1)."""
        # Valid name
        study = Study(name="A", instanceType="Study")
        assert study.name == "A"
        
        # Invalid empty name should raise validation error
        with pytest.raises(Exception):  # Pydantic validation error
            Study(name="", instanceType="Study")

    def test_with_versions_and_documents(self):
        """Test initialization with versions and documents."""
        # Create required codes and objects for StudyVersion
        from src.usdm4.api.identifier import StudyIdentifier
        from src.usdm4.api.study_title import StudyTitle
        
        version_status = Code(
            id="status1",
            code="ACTIVE",
            codeSystem="STATUS_SYSTEM",
            codeSystemVersion="1.0",
            decode="Active",
            instanceType="Code"
        )
        
        title_type = Code(
            id="title_type1",
            code="OFFICIAL",
            codeSystem="TITLE_TYPE",
            codeSystemVersion="1.0",
            decode="Official Title",
            instanceType="Code"
        )
        
        study_title = StudyTitle(
            id="title1",
            text="Test Study Title",
            type=title_type,
            instanceType="StudyTitle"
        )
        
        identifier_type = Code(
            id="id_type1",
            code="SPONSOR",
            codeSystem="ID_TYPE",
            codeSystemVersion="1.0",
            decode="Sponsor Identifier",
            instanceType="Code"
        )
        
        study_identifier = StudyIdentifier(
            id="identifier1",
            text="STUDY-001",
            type=identifier_type,
            scopeId="org1",
            instanceType="StudyIdentifier"
        )
        
        study_version = StudyVersion(
            id="version1",
            versionIdentifier="v1.0",
            rationale="Initial version",
            studyIdentifiers=[study_identifier],
            titles=[study_title],
            instanceType="StudyVersion"
        )
        
        # Create a study definition document
        doc_status = Code(
            id="doc_status1",
            code="FINAL",
            codeSystem="DOC_STATUS",
            codeSystemVersion="1.0",
            decode="Final",
            instanceType="Code"
        )
        
        doc_language = Code(
            id="lang1",
            code="EN",
            codeSystem="LANGUAGE",
            codeSystemVersion="1.0",
            decode="English",
            instanceType="Code"
        )
        
        doc_type = Code(
            id="doc_type1",
            code="PROTOCOL",
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode="Protocol Document",
            instanceType="Code"
        )
        
        study_doc = StudyDefinitionDocument(
            id="doc1",
            name="Protocol Document",
            label="Protocol v1.0",
            templateName="PROTOCOL",
            language=doc_language,
            type=doc_type,
            instanceType="StudyDefinitionDocument"
        )
        
        study_with_data = Study(
            name="Study with Data",
            versions=[study_version],
            documentedBy=[study_doc],
            instanceType="Study"
        )
        
        assert len(study_with_data.versions) == 1
        assert study_with_data.versions[0].versionIdentifier == "v1.0"
        assert len(study_with_data.documentedBy) == 1
        assert study_with_data.documentedBy[0].templateName == "PROTOCOL"

    def test_document_by_template_name_found(self):
        """Test document_by_template_name when document exists."""
        # Create study definition documents
        doc_language = Code(
            id="lang1",
            code="EN",
            codeSystem="LANGUAGE",
            codeSystemVersion="1.0",
            decode="English",
            instanceType="Code"
        )
        
        protocol_type = Code(
            id="protocol_type1",
            code="PROTOCOL",
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode="Protocol Document",
            instanceType="Code"
        )
        
        csr_type = Code(
            id="csr_type1",
            code="CSR",
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode="CSR Document",
            instanceType="Code"
        )
        
        protocol_doc = StudyDefinitionDocument(
            id="doc1",
            name="Protocol Document",
            label="Protocol v1.0",
            templateName="PROTOCOL",
            language=doc_language,
            type=protocol_type,
            instanceType="StudyDefinitionDocument"
        )
        
        csr_doc = StudyDefinitionDocument(
            id="doc2",
            name="CSR Document",
            label="CSR v1.0",
            templateName="CSR",
            language=doc_language,
            type=csr_type,
            instanceType="StudyDefinitionDocument"
        )
        
        self.study.documentedBy = [protocol_doc, csr_doc]
        
        # Test exact match
        result = self.study.document_by_template_name("PROTOCOL")
        assert result is not None
        assert result.templateName == "PROTOCOL"
        assert result.name == "Protocol Document"
        
        # Test case insensitive match
        result = self.study.document_by_template_name("protocol")
        assert result is not None
        assert result.templateName == "PROTOCOL"
        
        result = self.study.document_by_template_name("csr")
        assert result is not None
        assert result.templateName == "CSR"

    def test_document_by_template_name_not_found(self):
        """Test document_by_template_name when document doesn't exist."""
        # Create a study definition document
        doc_language = Code(
            id="lang1",
            code="EN",
            codeSystem="LANGUAGE",
            codeSystemVersion="1.0",
            decode="English",
            instanceType="Code"
        )
        
        protocol_type = Code(
            id="protocol_type1",
            code="PROTOCOL",
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode="Protocol Document",
            instanceType="Code"
        )
        
        protocol_doc = StudyDefinitionDocument(
            id="doc1",
            name="Protocol Document",
            label="Protocol v1.0",
            templateName="PROTOCOL",
            language=doc_language,
            type=protocol_type,
            instanceType="StudyDefinitionDocument"
        )
        
        self.study.documentedBy = [protocol_doc]
        
        # Test non-existent template name - this covers line 19
        result = self.study.document_by_template_name("NONEXISTENT")
        assert result is None
        
        # Test with empty list
        self.study.documentedBy = []
        result = self.study.document_by_template_name("PROTOCOL")
        assert result is None

    def test_first_version_with_versions(self):
        """Test first_version when versions exist."""
        # Create required objects for StudyVersion
        from src.usdm4.api.identifier import StudyIdentifier
        from src.usdm4.api.study_title import StudyTitle
        
        title_type = Code(
            id="title_type1",
            code="OFFICIAL",
            codeSystem="TITLE_TYPE",
            codeSystemVersion="1.0",
            decode="Official Title",
            instanceType="Code"
        )
        
        study_title = StudyTitle(
            id="title1",
            text="Test Study Title",
            type=title_type,
            instanceType="StudyTitle"
        )
        
        identifier_type = Code(
            id="id_type1",
            code="SPONSOR",
            codeSystem="ID_TYPE",
            codeSystemVersion="1.0",
            decode="Sponsor Identifier",
            instanceType="Code"
        )
        
        study_identifier = StudyIdentifier(
            id="identifier1",
            text="STUDY-001",
            type=identifier_type,
            scopeId="org1",
            instanceType="StudyIdentifier"
        )
        
        version1 = StudyVersion(
            id="version1",
            versionIdentifier="v1.0",
            rationale="Initial version",
            studyIdentifiers=[study_identifier],
            titles=[study_title],
            instanceType="StudyVersion"
        )
        
        version2 = StudyVersion(
            id="version2",
            versionIdentifier="v2.0",
            rationale="Second version",
            studyIdentifiers=[study_identifier],
            titles=[study_title],
            instanceType="StudyVersion"
        )
        
        self.study.versions = [version1, version2]
        
        # Test that first version is returned - this covers line 26
        result = self.study.first_version()
        assert result is not None
        assert result.versionIdentifier == "v1.0"
        assert result.id == "version1"

    def test_first_version_empty_list(self):
        """Test first_version when no versions exist."""
        # Empty versions list - this covers lines 27-28 (exception handling)
        self.study.versions = []
        result = self.study.first_version()
        assert result is None

    def test_first_version_exception_handling(self):
        """Test first_version exception handling."""
        # This test ensures the exception handling works
        # Even though accessing versions[0] on empty list would raise IndexError,
        # the try/except should catch it and return None
        self.study.versions = []
        result = self.study.first_version()
        assert result is None
        
        # Test with None versions (if somehow set to None)
        # This would be unusual but tests the exception handling
        try:
            # Temporarily set versions to None to test exception handling
            original_versions = self.study.versions
            self.study.versions = None
            result = self.study.first_version()
            assert result is None
        finally:
            # Restore original versions
            self.study.versions = original_versions

    def test_uuid_field_types(self):
        """Test that id field accepts UUID objects."""
        test_uuid = uuid4()
        study = Study(
            id=test_uuid,
            name="UUID Test Study",
            instanceType="Study"
        )
        
        assert study.id == test_uuid
        assert isinstance(study.id, UUID)

    def test_complex_scenario(self):
        """Test complex scenario with multiple versions and documents."""
        # Create multiple versions
        version_status = Code(
            id="status1",
            code="ACTIVE",
            codeSystem="STATUS_SYSTEM",
            codeSystemVersion="1.0",
            decode="Active",
            instanceType="Code"
        )
        
        # Create required objects for StudyVersion
        from src.usdm4.api.identifier import StudyIdentifier
        from src.usdm4.api.study_title import StudyTitle
        
        title_type = Code(
            id="title_type1",
            code="OFFICIAL",
            codeSystem="TITLE_TYPE",
            codeSystemVersion="1.0",
            decode="Official Title",
            instanceType="Code"
        )
        
        study_title = StudyTitle(
            id="title1",
            text="Test Study Title",
            type=title_type,
            instanceType="StudyTitle"
        )
        
        identifier_type = Code(
            id="id_type1",
            code="SPONSOR",
            codeSystem="ID_TYPE",
            codeSystemVersion="1.0",
            decode="Sponsor Identifier",
            instanceType="Code"
        )
        
        study_identifier = StudyIdentifier(
            id="identifier1",
            text="STUDY-001",
            type=identifier_type,
            scopeId="org1",
            instanceType="StudyIdentifier"
        )
        
        versions = []
        for i in range(3):
            version = StudyVersion(
                id=f"version{i+1}",
                versionIdentifier=f"v{i+1}.0",
                rationale=f"Version {i+1}",
                studyIdentifiers=[study_identifier],
                titles=[study_title],
                instanceType="StudyVersion"
            )
            versions.append(version)
        
        # Create multiple documents
        doc_language = Code(
            id="lang1",
            code="EN",
            codeSystem="LANGUAGE",
            codeSystemVersion="1.0",
            decode="English",
            instanceType="Code"
        )
        
        documents = []
        template_names = ["PROTOCOL", "CSR", "SAP"]
        for i, template in enumerate(template_names):
            doc_type = Code(
                id=f"doc_type{i+1}",
                code=template,
                codeSystem="DOC_TYPE",
                codeSystemVersion="1.0",
                decode=f"{template} Document",
                instanceType="Code"
            )
            
            doc = StudyDefinitionDocument(
                id=f"doc{i+1}",
                name=f"{template} Document",
                label=f"{template} v1.0",
                templateName=template,
                language=doc_language,
                type=doc_type,
                instanceType="StudyDefinitionDocument"
            )
            documents.append(doc)
        
        complex_study = Study(
            id=uuid4(),
            name="Complex Study",
            description="A complex study with multiple versions and documents",
            label="COMPLEX-001",
            versions=versions,
            documentedBy=documents,
            instanceType="Study"
        )
        
        # Test first_version
        first = complex_study.first_version()
        assert first is not None
        assert first.versionIdentifier == "v1.0"
        
        # Test document_by_template_name for each document
        for template in template_names:
            doc = complex_study.document_by_template_name(template)
            assert doc is not None
            assert doc.templateName == template
        
        # Test case insensitive search
        doc = complex_study.document_by_template_name("protocol")
        assert doc is not None
        assert doc.templateName == "PROTOCOL"
        
        # Test non-existent document
        doc = complex_study.document_by_template_name("NONEXISTENT")
        assert doc is None

    def test_edge_cases(self):
        """Test various edge cases."""
        # Test with special characters in name
        special_study = Study(
            name="Study with Special Characters: @#$%^&*()",
            instanceType="Study"
        )
        assert "Special Characters" in special_study.name
        
        # Test with very long name
        long_name = "A" * 1000
        long_study = Study(
            name=long_name,
            instanceType="Study"
        )
        assert len(long_study.name) == 1000
        
        # Test document search with empty string
        result = self.study.document_by_template_name("")
        assert result is None
        
        # Test document search with whitespace
        result = self.study.document_by_template_name("   ")
        assert result is None
