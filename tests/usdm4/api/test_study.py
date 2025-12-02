import pytest
from uuid import uuid4, UUID
from src.usdm4.api.study import Study
from src.usdm4.api.study_version import StudyVersion
from src.usdm4.api.study_definition_document import StudyDefinitionDocument
from src.usdm4.api.study_definition_document_version import (
    StudyDefinitionDocumentVersion,
)
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
            instanceType="Study",
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
        minimal_study = Study(name="Minimal Study", instanceType="Study")

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

        _ = Code(
            id="status1",
            code="ACTIVE",
            codeSystem="STATUS_SYSTEM",
            codeSystemVersion="1.0",
            decode="Active",
            instanceType="Code",
        )

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

        study_version = StudyVersion(
            id="version1",
            versionIdentifier="v1.0",
            rationale="Initial version",
            studyIdentifiers=[study_identifier],
            titles=[study_title],
            instanceType="StudyVersion",
        )

        # Create a study definition document
        _ = Code(
            id="doc_status1",
            code="FINAL",
            codeSystem="DOC_STATUS",
            codeSystemVersion="1.0",
            decode="Final",
            instanceType="Code",
        )

        doc_language = Code(
            id="lang1",
            code="EN",
            codeSystem="LANGUAGE",
            codeSystemVersion="1.0",
            decode="English",
            instanceType="Code",
        )

        doc_type = Code(
            id="doc_type1",
            code="PROTOCOL",
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode="Protocol Document",
            instanceType="Code",
        )

        study_doc = StudyDefinitionDocument(
            id="doc1",
            name="Protocol Document",
            label="Protocol v1.0",
            templateName="PROTOCOL",
            language=doc_language,
            type=doc_type,
            instanceType="StudyDefinitionDocument",
        )

        study_with_data = Study(
            name="Study with Data",
            versions=[study_version],
            documentedBy=[study_doc],
            instanceType="Study",
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
            instanceType="Code",
        )

        protocol_type = Code(
            id="protocol_type1",
            code="PROTOCOL",
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode="Protocol Document",
            instanceType="Code",
        )

        csr_type = Code(
            id="csr_type1",
            code="CSR",
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode="CSR Document",
            instanceType="Code",
        )

        protocol_doc = StudyDefinitionDocument(
            id="doc1",
            name="Protocol Document",
            label="Protocol v1.0",
            templateName="PROTOCOL",
            language=doc_language,
            type=protocol_type,
            instanceType="StudyDefinitionDocument",
        )

        csr_doc = StudyDefinitionDocument(
            id="doc2",
            name="CSR Document",
            label="CSR v1.0",
            templateName="CSR",
            language=doc_language,
            type=csr_type,
            instanceType="StudyDefinitionDocument",
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
            instanceType="Code",
        )

        protocol_type = Code(
            id="protocol_type1",
            code="PROTOCOL",
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode="Protocol Document",
            instanceType="Code",
        )

        protocol_doc = StudyDefinitionDocument(
            id="doc1",
            name="Protocol Document",
            label="Protocol v1.0",
            templateName="PROTOCOL",
            language=doc_language,
            type=protocol_type,
            instanceType="StudyDefinitionDocument",
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

        version1 = StudyVersion(
            id="version1",
            versionIdentifier="v1.0",
            rationale="Initial version",
            studyIdentifiers=[study_identifier],
            titles=[study_title],
            instanceType="StudyVersion",
        )

        version2 = StudyVersion(
            id="version2",
            versionIdentifier="v2.0",
            rationale="Second version",
            studyIdentifiers=[study_identifier],
            titles=[study_title],
            instanceType="StudyVersion",
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

    def test_first_version_single_version(self):
        """Test first_version returns the only version when there's just one."""
        # Create required objects for StudyVersion
        from src.usdm4.api.identifier import StudyIdentifier
        from src.usdm4.api.study_title import StudyTitle

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

        version1 = StudyVersion(
            id="version1",
            versionIdentifier="v1.0",
            rationale="Initial version",
            studyIdentifiers=[study_identifier],
            titles=[study_title],
            instanceType="StudyVersion",
        )

        self.study.versions = [version1]

        # Test that the single version is returned
        result = self.study.first_version()
        assert result is not None
        assert result.versionIdentifier == "v1.0"
        assert result.id == "version1"

    def test_uuid_field_types(self):
        """Test that id field accepts UUID objects."""
        test_uuid = uuid4()
        study = Study(id=test_uuid, name="UUID Test Study", instanceType="Study")

        assert study.id == test_uuid
        assert isinstance(study.id, UUID)

    def test_complex_scenario(self):
        """Test complex scenario with multiple versions and documents."""
        # Create multiple versions
        _ = Code(
            id="status1",
            code="ACTIVE",
            codeSystem="STATUS_SYSTEM",
            codeSystemVersion="1.0",
            decode="Active",
            instanceType="Code",
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

        versions = []
        for i in range(3):
            version = StudyVersion(
                id=f"version{i + 1}",
                versionIdentifier=f"v{i + 1}.0",
                rationale=f"Version {i + 1}",
                studyIdentifiers=[study_identifier],
                titles=[study_title],
                instanceType="StudyVersion",
            )
            versions.append(version)

        # Create multiple documents
        doc_language = Code(
            id="lang1",
            code="EN",
            codeSystem="LANGUAGE",
            codeSystemVersion="1.0",
            decode="English",
            instanceType="Code",
        )

        documents = []
        template_names = ["PROTOCOL", "CSR", "SAP"]
        for i, template in enumerate(template_names):
            doc_type = Code(
                id=f"doc_type{i + 1}",
                code=template,
                codeSystem="DOC_TYPE",
                codeSystemVersion="1.0",
                decode=f"{template} Document",
                instanceType="Code",
            )

            doc = StudyDefinitionDocument(
                id=f"doc{i + 1}",
                name=f"{template} Document",
                label=f"{template} v1.0",
                templateName=template,
                language=doc_language,
                type=doc_type,
                instanceType="StudyDefinitionDocument",
            )
            documents.append(doc)

        complex_study = Study(
            id=uuid4(),
            name="Complex Study",
            description="A complex study with multiple versions and documents",
            label="COMPLEX-001",
            versions=versions,
            documentedBy=documents,
            instanceType="Study",
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
            name="Study with Special Characters: @#$%^&*()", instanceType="Study"
        )
        assert "Special Characters" in special_study.name

        # Test with very long name
        long_name = "A" * 1000
        long_study = Study(name=long_name, instanceType="Study")
        assert len(long_study.name) == 1000

        # Test document search with empty string
        result = self.study.document_by_template_name("")
        assert result is None

        # Test document search with whitespace
        result = self.study.document_by_template_name("   ")
        assert result is None

    def test_document_templates_empty(self):
        """Test document_templates with no documents."""
        templates = self.study.document_templates()
        assert isinstance(templates, list)
        assert len(templates) == 0

    def test_document_templates_single_document(self):
        """Test document_templates with a single document."""
        doc_language = Code(
            id="lang1",
            code="EN",
            codeSystem="LANGUAGE",
            codeSystemVersion="1.0",
            decode="English",
            instanceType="Code",
        )

        protocol_type = Code(
            id="protocol_type1",
            code="PROTOCOL",
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode="Protocol Document",
            instanceType="Code",
        )

        protocol_doc = StudyDefinitionDocument(
            id="doc1",
            name="Protocol Document",
            label="Protocol v1.0",
            templateName="PROTOCOL",
            language=doc_language,
            type=protocol_type,
            instanceType="StudyDefinitionDocument",
        )

        self.study.documentedBy = [protocol_doc]
        templates = self.study.document_templates()

        assert isinstance(templates, list)
        assert len(templates) == 1
        assert templates[0] == "PROTOCOL"

    def test_document_templates_multiple_documents(self):
        """Test document_templates with multiple documents."""
        doc_language = Code(
            id="lang1",
            code="EN",
            codeSystem="LANGUAGE",
            codeSystemVersion="1.0",
            decode="English",
            instanceType="Code",
        )

        # Create multiple document types
        template_names = ["PROTOCOL", "CSR", "SAP", "ICF"]
        documents = []

        for i, template in enumerate(template_names):
            doc_type = Code(
                id=f"doc_type{i + 1}",
                code=template,
                codeSystem="DOC_TYPE",
                codeSystemVersion="1.0",
                decode=f"{template} Document",
                instanceType="Code",
            )

            doc = StudyDefinitionDocument(
                id=f"doc{i + 1}",
                name=f"{template} Document",
                label=f"{template} v1.0",
                templateName=template,
                language=doc_language,
                type=doc_type,
                instanceType="StudyDefinitionDocument",
            )
            documents.append(doc)

        self.study.documentedBy = documents
        templates = self.study.document_templates()

        assert isinstance(templates, list)
        assert len(templates) == 4
        assert templates == ["PROTOCOL", "CSR", "SAP", "ICF"]

    def test_document_templates_preserves_order(self):
        """Test that document_templates preserves the order of documents."""
        doc_language = Code(
            id="lang1",
            code="EN",
            codeSystem="LANGUAGE",
            codeSystemVersion="1.0",
            decode="English",
            instanceType="Code",
        )

        # Create documents in a specific order
        doc_type1 = Code(
            id="type1",
            code="CSR",
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode="CSR",
            instanceType="Code",
        )

        doc_type2 = Code(
            id="type2",
            code="PROTOCOL",
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode="Protocol",
            instanceType="Code",
        )

        doc_type3 = Code(
            id="type3",
            code="SAP",
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode="SAP",
            instanceType="Code",
        )

        doc1 = StudyDefinitionDocument(
            id="doc1",
            name="CSR Document",
            label="CSR v1.0",
            templateName="CSR",
            language=doc_language,
            type=doc_type1,
            instanceType="StudyDefinitionDocument",
        )

        doc2 = StudyDefinitionDocument(
            id="doc2",
            name="Protocol Document",
            label="Protocol v1.0",
            templateName="PROTOCOL",
            language=doc_language,
            type=doc_type2,
            instanceType="StudyDefinitionDocument",
        )

        doc3 = StudyDefinitionDocument(
            id="doc3",
            name="SAP Document",
            label="SAP v1.0",
            templateName="SAP",
            language=doc_language,
            type=doc_type3,
            instanceType="StudyDefinitionDocument",
        )

        # Add in specific order: CSR, PROTOCOL, SAP
        self.study.documentedBy = [doc1, doc2, doc3]
        templates = self.study.document_templates()

        # Should preserve this exact order
        assert templates == ["CSR", "PROTOCOL", "SAP"]

    def test_document_templates_with_duplicate_names(self):
        """Test document_templates when documents have duplicate template names."""
        doc_language = Code(
            id="lang1",
            code="EN",
            codeSystem="LANGUAGE",
            codeSystemVersion="1.0",
            decode="English",
            instanceType="Code",
        )

        protocol_type = Code(
            id="protocol_type1",
            code="PROTOCOL",
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode="Protocol Document",
            instanceType="Code",
        )

        # Create two documents with the same template name
        doc1 = StudyDefinitionDocument(
            id="doc1",
            name="Protocol Document v1",
            label="Protocol v1.0",
            templateName="PROTOCOL",
            language=doc_language,
            type=protocol_type,
            instanceType="StudyDefinitionDocument",
        )

        doc2 = StudyDefinitionDocument(
            id="doc2",
            name="Protocol Document v2",
            label="Protocol v2.0",
            templateName="PROTOCOL",
            language=doc_language,
            type=protocol_type,
            instanceType="StudyDefinitionDocument",
        )

        self.study.documentedBy = [doc1, doc2]
        templates = self.study.document_templates()

        # Should return both, even if they're duplicates
        assert len(templates) == 2
        assert templates == ["PROTOCOL", "PROTOCOL"]

    def test_document_templates_case_sensitivity(self):
        """Test that document_templates preserves the case of template names."""
        doc_language = Code(
            id="lang1",
            code="EN",
            codeSystem="LANGUAGE",
            codeSystemVersion="1.0",
            decode="English",
            instanceType="Code",
        )

        # Create documents with different case variations
        doc_type1 = Code(
            id="type1",
            code="PROTOCOL",
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode="Protocol",
            instanceType="Code",
        )

        doc_type2 = Code(
            id="type2",
            code="protocol",
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode="protocol",
            instanceType="Code",
        )

        doc1 = StudyDefinitionDocument(
            id="doc1",
            name="Protocol Upper",
            label="Protocol v1.0",
            templateName="PROTOCOL",
            language=doc_language,
            type=doc_type1,
            instanceType="StudyDefinitionDocument",
        )

        doc2 = StudyDefinitionDocument(
            id="doc2",
            name="Protocol Lower",
            label="protocol v1.0",
            templateName="protocol",
            language=doc_language,
            type=doc_type2,
            instanceType="StudyDefinitionDocument",
        )

        self.study.documentedBy = [doc1, doc2]
        templates = self.study.document_templates()

        # Should preserve the original case
        assert templates == ["PROTOCOL", "protocol"]

    # =====================================================
    # Tests for document_map method
    # =====================================================

    def _create_document_version(
        self, version_id: str, version_number: str = "1.0"
    ) -> StudyDefinitionDocumentVersion:
        """Helper method to create a StudyDefinitionDocumentVersion."""
        status_code = Code(
            id="status1",
            code="FINAL",
            codeSystem="DOC_STATUS",
            codeSystemVersion="1.0",
            decode="Final",
            instanceType="Code",
        )

        return StudyDefinitionDocumentVersion(
            id=version_id,
            version=version_number,
            status=status_code,
            instanceType="StudyDefinitionDocumentVersion",
        )

    def _create_document_with_versions(
        self, doc_id: str, template_name: str, versions: list
    ) -> StudyDefinitionDocument:
        """Helper method to create a StudyDefinitionDocument with versions."""
        doc_language = Code(
            id="lang1",
            code="EN",
            codeSystem="LANGUAGE",
            codeSystemVersion="1.0",
            decode="English",
            instanceType="Code",
        )

        doc_type = Code(
            id=f"doc_type_{doc_id}",
            code=template_name,
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode=f"{template_name} Document",
            instanceType="Code",
        )

        return StudyDefinitionDocument(
            id=doc_id,
            name=f"{template_name} Document",
            label=f"{template_name} v1.0",
            templateName=template_name,
            language=doc_language,
            type=doc_type,
            versions=versions,
            instanceType="StudyDefinitionDocument",
        )

    def test_document_map_empty_documents(self):
        """Test document_map with no documents."""
        self.study.documentedBy = []

        result = self.study.document_map()

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_document_map_document_without_versions(self):
        """Test document_map with a document that has no versions."""
        doc = self._create_document_with_versions("doc1", "PROTOCOL", [])
        self.study.documentedBy = [doc]

        result = self.study.document_map()

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_document_map_single_document_single_version(self):
        """Test document_map with a single document that has one version."""
        version = self._create_document_version("version1", "1.0")
        doc = self._create_document_with_versions("doc1", "PROTOCOL", [version])
        self.study.documentedBy = [doc]

        result = self.study.document_map()

        assert isinstance(result, dict)
        assert len(result) == 1
        assert "version1" in result
        assert "document" in result["version1"]
        assert "version" in result["version1"]
        assert result["version1"]["document"] == doc
        assert result["version1"]["version"] == version
        assert result["version1"]["version"].version == "1.0"

    def test_document_map_single_document_multiple_versions(self):
        """Test document_map with a single document that has multiple versions."""
        version1 = self._create_document_version("version1", "1.0")
        version2 = self._create_document_version("version2", "2.0")
        version3 = self._create_document_version("version3", "3.0")
        doc = self._create_document_with_versions(
            "doc1", "PROTOCOL", [version1, version2, version3]
        )
        self.study.documentedBy = [doc]

        result = self.study.document_map()

        assert isinstance(result, dict)
        assert len(result) == 3
        assert "version1" in result
        assert "version2" in result
        assert "version3" in result
        assert result["version1"]["version"].version == "1.0"
        assert result["version2"]["version"].version == "2.0"
        assert result["version3"]["version"].version == "3.0"
        # All versions should reference the same document
        assert result["version1"]["document"] == doc
        assert result["version2"]["document"] == doc
        assert result["version3"]["document"] == doc

    def test_document_map_multiple_documents_single_version_each(self):
        """Test document_map with multiple documents, each having one version."""
        version1 = self._create_document_version("protocol_v1", "1.0")
        version2 = self._create_document_version("csr_v1", "1.0")
        version3 = self._create_document_version("sap_v1", "1.0")

        doc1 = self._create_document_with_versions("doc1", "PROTOCOL", [version1])
        doc2 = self._create_document_with_versions("doc2", "CSR", [version2])
        doc3 = self._create_document_with_versions("doc3", "SAP", [version3])

        self.study.documentedBy = [doc1, doc2, doc3]

        result = self.study.document_map()

        assert isinstance(result, dict)
        assert len(result) == 3
        assert "protocol_v1" in result
        assert "csr_v1" in result
        assert "sap_v1" in result
        # Each version should reference its own document
        assert result["protocol_v1"]["document"] == doc1
        assert result["csr_v1"]["document"] == doc2
        assert result["sap_v1"]["document"] == doc3

    def test_document_map_multiple_documents_multiple_versions(self):
        """Test document_map with multiple documents, each having multiple versions."""
        # Protocol document versions
        protocol_v1 = self._create_document_version("protocol_v1", "1.0")
        protocol_v2 = self._create_document_version("protocol_v2", "2.0")

        # CSR document versions
        csr_v1 = self._create_document_version("csr_v1", "1.0")
        csr_v2 = self._create_document_version("csr_v2", "2.0")
        csr_v3 = self._create_document_version("csr_v3", "3.0")

        doc1 = self._create_document_with_versions(
            "doc1", "PROTOCOL", [protocol_v1, protocol_v2]
        )
        doc2 = self._create_document_with_versions(
            "doc2", "CSR", [csr_v1, csr_v2, csr_v3]
        )

        self.study.documentedBy = [doc1, doc2]

        result = self.study.document_map()

        assert isinstance(result, dict)
        assert len(result) == 5
        assert "protocol_v1" in result
        assert "protocol_v2" in result
        assert "csr_v1" in result
        assert "csr_v2" in result
        assert "csr_v3" in result
        # Protocol versions reference doc1
        assert result["protocol_v1"]["document"] == doc1
        assert result["protocol_v2"]["document"] == doc1
        # CSR versions reference doc2
        assert result["csr_v1"]["document"] == doc2
        assert result["csr_v2"]["document"] == doc2
        assert result["csr_v3"]["document"] == doc2

    def test_document_map_returns_correct_version_objects(self):
        """Test that document_map returns the actual version and document objects."""
        version = self._create_document_version("version1", "1.0")
        doc = self._create_document_with_versions("doc1", "PROTOCOL", [version])
        self.study.documentedBy = [doc]

        result = self.study.document_map()

        # Verify it's the same objects
        assert result["version1"]["version"] is version
        assert result["version1"]["document"] is doc
        assert isinstance(result["version1"]["version"], StudyDefinitionDocumentVersion)
        assert isinstance(result["version1"]["document"], StudyDefinitionDocument)

    def test_document_map_with_mixed_empty_and_populated_documents(self):
        """Test document_map with a mix of documents, some with versions and some without."""
        version1 = self._create_document_version("version1", "1.0")
        version2 = self._create_document_version("version2", "2.0")

        # Doc1 has versions
        doc1 = self._create_document_with_versions("doc1", "PROTOCOL", [version1])
        # Doc2 has no versions
        doc2 = self._create_document_with_versions("doc2", "CSR", [])
        # Doc3 has versions
        doc3 = self._create_document_with_versions("doc3", "SAP", [version2])

        self.study.documentedBy = [doc1, doc2, doc3]

        result = self.study.document_map()

        assert len(result) == 2
        assert "version1" in result
        assert "version2" in result
        # Verify correct document association
        assert result["version1"]["document"] == doc1
        assert result["version2"]["document"] == doc3

    def test_document_map_preserves_version_properties(self):
        """Test that document_map preserves all version and document properties."""
        status_code = Code(
            id="status1",
            code="DRAFT",
            codeSystem="DOC_STATUS",
            codeSystemVersion="1.0",
            decode="Draft",
            instanceType="Code",
        )

        version = StudyDefinitionDocumentVersion(
            id="version1",
            version="1.5.3",
            status=status_code,
            instanceType="StudyDefinitionDocumentVersion",
        )

        doc = self._create_document_with_versions("doc1", "PROTOCOL", [version])
        self.study.documentedBy = [doc]

        result = self.study.document_map()

        # Verify version properties
        assert result["version1"]["version"].version == "1.5.3"
        assert result["version1"]["version"].status.code == "DRAFT"
        assert result["version1"]["version"].status.decode == "Draft"
        # Verify document properties
        assert result["version1"]["document"].templateName == "PROTOCOL"
        assert result["version1"]["document"].id == "doc1"
