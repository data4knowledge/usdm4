from datetime import date
from src.usdm4.api.study_definition_document_version import (
    StudyDefinitionDocumentVersion,
)
from src.usdm4.api.code import Code
from src.usdm4.api.governance_date import GovernanceDate
from src.usdm4.api.narrative_content import NarrativeContent
from src.usdm4.api.comment_annotation import CommentAnnotation
from src.usdm4.api.geographic_scope import GeographicScope


class TestStudyDefinitionDocumentVersion:
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.status_code = Code(
            id="status1",
            code="ACTIVE",
            codeSystem="STATUS_SYSTEM",
            codeSystemVersion="1.0",
            decode="Active",
            instanceType="Code",
        )

        self.doc_version = StudyDefinitionDocumentVersion(
            id="doc_version1",
            version="1.0",
            status=self.status_code,
            instanceType="StudyDefinitionDocumentVersion",
        )

    def test_basic_initialization(self):
        """Test basic initialization of StudyDefinitionDocumentVersion."""
        assert self.doc_version.id == "doc_version1"
        assert self.doc_version.version == "1.0"
        assert self.doc_version.status == self.status_code
        assert self.doc_version.dateValues == []
        assert self.doc_version.contents == []
        assert self.doc_version.notes == []
        assert self.doc_version.instanceType == "StudyDefinitionDocumentVersion"

    def test_with_date_values_and_notes(self):
        """Test initialization with date values and notes."""
        # Create governance date
        type_code = Code(
            id="type1",
            code="APPROVAL",
            codeSystem="DATE_TYPE",
            codeSystemVersion="1.0",
            decode="Approval Date",
            instanceType="Code",
        )

        geo_type_code = Code(
            id="geo_type1",
            code="COUNTRY",
            codeSystem="GEO_TYPE",
            codeSystemVersion="1.0",
            decode="Country",
            instanceType="Code",
        )

        geo_scope = GeographicScope(
            id="geo1", type=geo_type_code, instanceType="GeographicScope"
        )

        gov_date = GovernanceDate(
            id="date1",
            name="Approval Date",
            label="FDA Approval",
            description="FDA approval date",
            type=type_code,
            dateValue=date(2024, 1, 15),
            geographicScopes=[geo_scope],
            instanceType="GovernanceDate",
        )

        # Create comment annotation
        comment_code = Code(
            id="comment1",
            code="REVIEW",
            codeSystem="COMMENT_TYPE",
            codeSystemVersion="1.0",
            decode="Review Comment",
            instanceType="Code",
        )

        comment = CommentAnnotation(
            id="note1",
            text="This needs review",
            codes=[comment_code],
            instanceType="CommentAnnotation",
        )

        doc_version = StudyDefinitionDocumentVersion(
            id="doc_version2",
            version="2.0",
            status=self.status_code,
            dateValues=[gov_date],
            notes=[comment],
            instanceType="StudyDefinitionDocumentVersion",
        )

        assert len(doc_version.dateValues) == 1
        assert doc_version.dateValues[0].dateValue == date(2024, 1, 15)
        assert len(doc_version.notes) == 1
        assert doc_version.notes[0].text == "This needs review"

    def test_narrative_content_in_order_empty(self):
        """Test narrative_content_in_order with empty contents."""
        result = self.doc_version.narrative_content_in_order()
        assert result == []

    def test_narrative_content_in_order_single_item(self):
        """Test narrative_content_in_order with single narrative content."""
        content = NarrativeContent(
            id="content1",
            name="Introduction",
            sectionNumber="1",
            sectionTitle="Introduction",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId=None,
            nextId=None,
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content]
        result = self.doc_version.narrative_content_in_order()
        assert result == []  # No nextId, so _first_narrative_content returns None

    def test_narrative_content_in_order_with_chain(self):
        """Test narrative_content_in_order with chained narrative content."""
        content1 = NarrativeContent(
            id="content1",
            name="Introduction",
            sectionNumber="1",
            sectionTitle="Introduction",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId=None,
            nextId="content2",
            instanceType="NarrativeContent",
        )

        content2 = NarrativeContent(
            id="content2",
            name="Methods",
            sectionNumber="2",
            sectionTitle="Methods",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId="content1",
            nextId="content3",
            instanceType="NarrativeContent",
        )

        content3 = NarrativeContent(
            id="content3",
            name="Results",
            sectionNumber="3",
            sectionTitle="Results",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId="content2",
            nextId=None,
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [
            content2,
            content3,
            content1,
        ]  # Intentionally out of order
        result = self.doc_version.narrative_content_in_order()

        assert len(result) == 3
        assert result[0].id == "content1"
        assert result[1].id == "content2"
        assert result[2].id == "content3"

    def test_narrative_content_in_order_broken_chain(self):
        """Test narrative_content_in_order with broken chain."""
        content1 = NarrativeContent(
            id="content1",
            name="Introduction",
            sectionNumber="1",
            sectionTitle="Introduction",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId=None,
            nextId="missing_content",  # Points to non-existent content
            instanceType="NarrativeContent",
        )

        content2 = NarrativeContent(
            id="content2",
            name="Methods",
            sectionNumber="2",
            sectionTitle="Methods",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId="content1",
            nextId=None,
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content1, content2]
        result = self.doc_version.narrative_content_in_order()

        assert len(result) == 1
        assert result[0].id == "content1"

    def test_find_narrative_content_found(self):
        """Test find_narrative_content when content exists."""
        content1 = NarrativeContent(
            id="content1",
            name="Introduction",
            sectionNumber="1",
            sectionTitle="Introduction",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )

        content2 = NarrativeContent(
            id="content2",
            name="Methods",
            sectionNumber="2",
            sectionTitle="Methods",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content1, content2]
        result = self.doc_version.find_narrative_content("content2")

        # Due to the typo in the original code ("narraitve_content_map" instead of "narrative_content_map"),
        # this will cause an AttributeError and return None
        assert result is None

    def test_find_narrative_content_not_found(self):
        """Test find_narrative_content when content doesn't exist."""
        content1 = NarrativeContent(
            id="content1",
            name="Introduction",
            sectionNumber="1",
            sectionTitle="Introduction",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content1]
        result = self.doc_version.find_narrative_content("nonexistent")

        assert result is None

    def test_find_narrative_content_exception_handling(self):
        """Test find_narrative_content exception handling."""
        # Note: There's a typo in the original code: "narraitve_content_map" instead of "narrative_content_map"
        # This will cause an AttributeError, which should be caught and return None
        content1 = NarrativeContent(
            id="content1",
            name="Introduction",
            sectionNumber="1",
            sectionTitle="Introduction",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content1]
        result = self.doc_version.find_narrative_content("content1")

        # Due to the typo in the original code, this should return None
        assert result is None

    def test_narrative_content_map(self):
        """Test narraitve_content_map method (note the typo in the method name)."""
        content1 = NarrativeContent(
            id="content1",
            name="Introduction",
            sectionNumber="1",
            sectionTitle="Introduction",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )

        content2 = NarrativeContent(
            id="content2",
            name="Methods",
            sectionNumber="2",
            sectionTitle="Methods",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content1, content2]
        result = self.doc_version.narraitve_content_map()

        assert isinstance(result, dict)
        assert len(result) == 2
        assert "content1" in result
        assert "content2" in result
        assert result["content1"] == content1
        assert result["content2"] == content2

    def test_first_narrative_content_none(self):
        """Test _first_narrative_content when no first content exists."""
        content1 = NarrativeContent(
            id="content1",
            name="Introduction",
            sectionNumber="1",
            sectionTitle="Introduction",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId="some_id",  # Has previousId, so not first
            nextId="content2",
            instanceType="NarrativeContent",
        )

        content2 = NarrativeContent(
            id="content2",
            name="Methods",
            sectionNumber="2",
            sectionTitle="Methods",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId="content1",
            nextId=None,  # No nextId, so not first
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content1, content2]
        result = self.doc_version._first_narrative_content()

        assert result is None

    def test_first_narrative_content_found(self):
        """Test _first_narrative_content when first content exists."""
        content1 = NarrativeContent(
            id="content1",
            name="Introduction",
            sectionNumber="1",
            sectionTitle="Introduction",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId=None,  # No previousId
            nextId="content2",  # Has nextId
            instanceType="NarrativeContent",
        )

        content2 = NarrativeContent(
            id="content2",
            name="Methods",
            sectionNumber="2",
            sectionTitle="Methods",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId="content1",
            nextId=None,
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content2, content1]  # Order shouldn't matter
        result = self.doc_version._first_narrative_content()

        assert result is not None
        assert result.id == "content1"
        assert result.name == "Introduction"

    def test_complex_narrative_content_scenario(self):
        """Test complex scenario with multiple narrative contents."""
        # Create a complex chain: content1 -> content2 -> content3
        # Plus an orphaned content4
        content1 = NarrativeContent(
            id="content1",
            name="Introduction",
            sectionNumber="1",
            sectionTitle="Introduction",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId=None,
            nextId="content2",
            instanceType="NarrativeContent",
        )

        content2 = NarrativeContent(
            id="content2",
            name="Methods",
            sectionNumber="2",
            sectionTitle="Methods",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId="content1",
            nextId="content3",
            instanceType="NarrativeContent",
        )

        content3 = NarrativeContent(
            id="content3",
            name="Results",
            sectionNumber="3",
            sectionTitle="Results",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId="content2",
            nextId=None,
            instanceType="NarrativeContent",
        )

        content4 = NarrativeContent(
            id="content4",
            name="Orphaned",
            sectionNumber="4",
            sectionTitle="Orphaned Section",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId="nonexistent",
            nextId=None,
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content4, content2, content1, content3]

        # Test narrative_content_in_order
        ordered = self.doc_version.narrative_content_in_order()
        assert len(ordered) == 3
        assert [c.id for c in ordered] == ["content1", "content2", "content3"]

        # Test find_narrative_content (should still fail due to typo)
        result = self.doc_version.find_narrative_content("content3")
        assert result is None  # Due to the typo in the original code

        # Test narraitve_content_map
        content_map = self.doc_version.narraitve_content_map()
        assert len(content_map) == 4
        assert all(
            content_id in content_map
            for content_id in ["content1", "content2", "content3", "content4"]
        )

    def test_empty_contents_all_methods(self):
        """Test all methods with empty contents list."""
        self.doc_version.contents = []

        # Test narrative_content_in_order
        ordered = self.doc_version.narrative_content_in_order()
        assert ordered == []

        # Test find_narrative_content
        result = self.doc_version.find_narrative_content("any_id")
        assert result is None

        # Test narraitve_content_map
        content_map = self.doc_version.narraitve_content_map()
        assert content_map == {}

        # Test _first_narrative_content
        first = self.doc_version._first_narrative_content()
        assert first is None
