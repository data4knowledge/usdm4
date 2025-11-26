import pytest
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

    def test_with_date_values(self):
        """Test initialization with date values."""
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

        doc_version = StudyDefinitionDocumentVersion(
            id="doc_version2",
            version="2.0",
            status=self.status_code,
            dateValues=[gov_date],
            instanceType="StudyDefinitionDocumentVersion",
        )

        assert len(doc_version.dateValues) == 1
        assert doc_version.dateValues[0].dateValue == date(2024, 1, 15)
        assert doc_version.dateValues[0].name == "Approval Date"

    def test_with_notes(self):
        """Test initialization with comment annotations."""
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
            id="doc_version3",
            version="1.5",
            status=self.status_code,
            notes=[comment],
            instanceType="StudyDefinitionDocumentVersion",
        )

        assert len(doc_version.notes) == 1
        assert doc_version.notes[0].text == "This needs review"
        assert doc_version.notes[0].codes[0].code == "REVIEW"

    def test_multiple_date_values_and_notes(self):
        """Test initialization with multiple date values and notes."""
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

        gov_date1 = GovernanceDate(
            id="date1",
            name="Approval Date",
            label="FDA Approval",
            type=type_code,
            dateValue=date(2024, 1, 15),
            geographicScopes=[geo_scope],
            instanceType="GovernanceDate",
        )

        gov_date2 = GovernanceDate(
            id="date2",
            name="Submission Date",
            label="FDA Submission",
            type=type_code,
            dateValue=date(2024, 1, 1),
            geographicScopes=[geo_scope],
            instanceType="GovernanceDate",
        )

        comment_code = Code(
            id="comment1",
            code="REVIEW",
            codeSystem="COMMENT_TYPE",
            codeSystemVersion="1.0",
            decode="Review Comment",
            instanceType="Code",
        )

        comment1 = CommentAnnotation(
            id="note1",
            text="First review comment",
            codes=[comment_code],
            instanceType="CommentAnnotation",
        )

        comment2 = CommentAnnotation(
            id="note2",
            text="Second review comment",
            codes=[comment_code],
            instanceType="CommentAnnotation",
        )

        doc_version = StudyDefinitionDocumentVersion(
            id="doc_version4",
            version="2.0",
            status=self.status_code,
            dateValues=[gov_date1, gov_date2],
            notes=[comment1, comment2],
            instanceType="StudyDefinitionDocumentVersion",
        )

        assert len(doc_version.dateValues) == 2
        assert len(doc_version.notes) == 2

    # Tests for narrative_content_in_order()
    def test_narrative_content_in_order_empty(self):
        """Test narrative_content_in_order with empty contents."""
        result = self.doc_version.narrative_content_in_order()
        assert result == []

    def test_narrative_content_in_order_single_item_with_next(self):
        """Test narrative_content_in_order with single narrative content with nextId."""
        content = NarrativeContent(
            id="content1",
            name="Introduction",
            sectionNumber="1",
            sectionTitle="Introduction",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId=None,
            nextId="content2",  # Points to non-existent content
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content]
        result = self.doc_version.narrative_content_in_order()
        assert len(result) == 1
        assert result[0].id == "content1"

    def test_narrative_content_in_order_single_item_no_next(self):
        """Test narrative_content_in_order with single narrative content without nextId."""
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

    def test_narrative_content_in_order_multiple_chains(self):
        """Test narrative_content_in_order when there are multiple chains."""
        # Chain 1: content1 -> content2
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
            nextId=None,
            instanceType="NarrativeContent",
        )

        # Chain 2: content3 -> content4 (orphaned chain)
        content3 = NarrativeContent(
            id="content3",
            name="Appendix A",
            sectionNumber="A",
            sectionTitle="Appendix A",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId=None,
            nextId="content4",
            instanceType="NarrativeContent",
        )

        content4 = NarrativeContent(
            id="content4",
            name="Appendix B",
            sectionNumber="B",
            sectionTitle="Appendix B",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId="content3",
            nextId=None,
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content4, content2, content3, content1]
        result = self.doc_version.narrative_content_in_order()

        # _first_narrative_content returns the first item in the list that matches
        # (no previousId and has nextId), which is content3 in this case
        assert len(result) == 2
        assert result[0].id == "content3"
        assert result[1].id == "content4"

    # Tests for find_narrative_content()
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

        assert result is not None
        assert result.id == "content2"
        assert result.name == "Methods"

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

    def test_find_narrative_content_empty_contents(self):
        """Test find_narrative_content with empty contents."""
        self.doc_version.contents = []
        result = self.doc_version.find_narrative_content("any_id")
        assert result is None

    def test_find_narrative_content_first_item(self):
        """Test find_narrative_content for the first item in contents."""
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
        result = self.doc_version.find_narrative_content("content1")

        assert result is not None
        assert result.id == "content1"

    # Tests for find_narrative_content_by_number()
    def test_find_narrative_content_by_number_found(self):
        """Test find_narrative_content_by_number when content exists."""
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
            sectionNumber="2.1",
            sectionTitle="Methods",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content1, content2]
        result = self.doc_version.find_narrative_content_by_number("2.1")

        assert result is not None
        assert result.id == "content2"
        assert result.sectionNumber == "2.1"

    def test_find_narrative_content_by_number_not_found(self):
        """Test find_narrative_content_by_number when content doesn't exist."""
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
        result = self.doc_version.find_narrative_content_by_number("99")

        assert result is None

    def test_find_narrative_content_by_number_empty_contents(self):
        """Test find_narrative_content_by_number with empty contents."""
        self.doc_version.contents = []
        result = self.doc_version.find_narrative_content_by_number("1")
        assert result is None

    def test_find_narrative_content_by_number_none_section_number(self):
        """Test find_narrative_content_by_number when section_number is None."""
        content1 = NarrativeContent(
            id="content1",
            name="Introduction",
            sectionNumber=None,
            sectionTitle="Introduction",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content1]
        result = self.doc_version.find_narrative_content_by_number("1")

        assert result is None

    def test_find_narrative_content_by_number_multiple_matches(self):
        """Test find_narrative_content_by_number returns first match."""
        content1 = NarrativeContent(
            id="content1",
            name="Introduction",
            sectionNumber="1",
            sectionTitle="Introduction",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )

        # Duplicate section number (shouldn't happen in practice, but test it)
        content2 = NarrativeContent(
            id="content2",
            name="Another Introduction",
            sectionNumber="1",
            sectionTitle="Another Introduction",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content1, content2]
        result = self.doc_version.find_narrative_content_by_number("1")

        assert result is not None
        assert result.id == "content1"  # Should return the first match

    # Tests for find_narrative_content_by_title()
    def test_find_narrative_content_by_title_found(self):
        """Test find_narrative_content_by_title when content exists."""
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
            sectionTitle="Study Methods",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content1, content2]
        result = self.doc_version.find_narrative_content_by_title("Study Methods")

        assert result is not None
        assert result.id == "content2"
        assert result.sectionTitle == "Study Methods"

    def test_find_narrative_content_by_title_case_insensitive(self):
        """Test find_narrative_content_by_title is case insensitive."""
        content1 = NarrativeContent(
            id="content1",
            name="Introduction",
            sectionNumber="1",
            sectionTitle="Introduction Section",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content1]

        # Test various case combinations
        result1 = self.doc_version.find_narrative_content_by_title("introduction section")
        result2 = self.doc_version.find_narrative_content_by_title("INTRODUCTION SECTION")
        result3 = self.doc_version.find_narrative_content_by_title("InTrOdUcTiOn SeCtiOn")

        assert result1 is not None and result1.id == "content1"
        assert result2 is not None and result2.id == "content1"
        assert result3 is not None and result3.id == "content1"

    def test_find_narrative_content_by_title_not_found(self):
        """Test find_narrative_content_by_title when content doesn't exist."""
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
        result = self.doc_version.find_narrative_content_by_title("Nonexistent Title")

        assert result is None

    def test_find_narrative_content_by_title_empty_contents(self):
        """Test find_narrative_content_by_title with empty contents."""
        self.doc_version.contents = []
        result = self.doc_version.find_narrative_content_by_title("Any Title")
        assert result is None

    def test_find_narrative_content_by_title_none_section_title(self):
        """Test find_narrative_content_by_title when section_title is None.
        
        Note: This test reveals a bug in the source code - it doesn't handle None values.
        The code will raise AttributeError when trying to call .upper() on None.
        """
        content1 = NarrativeContent(
            id="content1",
            name="Introduction",
            sectionNumber="1",
            sectionTitle=None,
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content1]
        
        # The source code has a bug - it will raise AttributeError when sectionTitle is None
        with pytest.raises(AttributeError):
            self.doc_version.find_narrative_content_by_title("Introduction")

    def test_find_narrative_content_by_title_multiple_matches(self):
        """Test find_narrative_content_by_title returns first match."""
        content1 = NarrativeContent(
            id="content1",
            name="Introduction",
            sectionNumber="1",
            sectionTitle="Methods",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )

        # Duplicate section title (shouldn't happen in practice, but test it)
        content2 = NarrativeContent(
            id="content2",
            name="Another Methods",
            sectionNumber="2",
            sectionTitle="Methods",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content1, content2]
        result = self.doc_version.find_narrative_content_by_title("Methods")

        assert result is not None
        assert result.id == "content1"  # Should return the first match

    # Tests for narrative_content_map()
    def test_narrative_content_map_empty(self):
        """Test narrative_content_map with empty contents."""
        self.doc_version.contents = []
        result = self.doc_version.narrative_content_map()

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_narrative_content_map_single_item(self):
        """Test narrative_content_map with single content."""
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
        result = self.doc_version.narrative_content_map()

        assert isinstance(result, dict)
        assert len(result) == 1
        assert "content1" in result
        assert result["content1"] == content1

    def test_narrative_content_map_multiple_items(self):
        """Test narrative_content_map with multiple contents."""
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

        content3 = NarrativeContent(
            id="content3",
            name="Results",
            sectionNumber="3",
            sectionTitle="Results",
            displaySectionNumber=True,
            displaySectionTitle=True,
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content1, content2, content3]
        result = self.doc_version.narrative_content_map()

        assert isinstance(result, dict)
        assert len(result) == 3
        assert "content1" in result
        assert "content2" in result
        assert "content3" in result
        assert result["content1"] == content1
        assert result["content2"] == content2
        assert result["content3"] == content3

    # Tests for _first_narrative_content()
    def test_first_narrative_content_none_empty_contents(self):
        """Test _first_narrative_content with empty contents."""
        self.doc_version.contents = []
        result = self.doc_version._first_narrative_content()
        assert result is None

    def test_first_narrative_content_no_first(self):
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

    def test_first_narrative_content_with_multiple_candidates(self):
        """Test _first_narrative_content returns the first match."""
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

        # This is also a "first" (no previousId and has nextId) - orphaned chain
        content3 = NarrativeContent(
            id="content3",
            name="Appendix",
            sectionNumber="A",
            sectionTitle="Appendix",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId=None,
            nextId="content4",
            instanceType="NarrativeContent",
        )

        self.doc_version.contents = [content1, content2, content3]
        result = self.doc_version._first_narrative_content()

        # Should return the first occurrence that matches criteria
        assert result is not None
        assert result.id == "content1"

    # Integration tests
    def test_complex_scenario_with_all_methods(self):
        """Test complex scenario using all methods together."""
        # Create a complex chain: content1 -> content2 -> content3
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
            sectionTitle="Methods and Materials",
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

        self.doc_version.contents = [content3, content1, content2]

        # Test narrative_content_in_order
        ordered = self.doc_version.narrative_content_in_order()
        assert len(ordered) == 3
        assert [c.id for c in ordered] == ["content1", "content2", "content3"]

        # Test find_narrative_content
        found = self.doc_version.find_narrative_content("content2")
        assert found is not None
        assert found.name == "Methods"

        # Test find_narrative_content_by_number
        found_by_num = self.doc_version.find_narrative_content_by_number("2")
        assert found_by_num is not None
        assert found_by_num.id == "content2"

        # Test find_narrative_content_by_title
        found_by_title = self.doc_version.find_narrative_content_by_title("methods and materials")
        assert found_by_title is not None
        assert found_by_title.id == "content2"

        # Test narrative_content_map
        content_map = self.doc_version.narrative_content_map()
        assert len(content_map) == 3
        assert all(id in content_map for id in ["content1", "content2", "content3"])

        # Test _first_narrative_content
        first = self.doc_version._first_narrative_content()
        assert first is not None
        assert first.id == "content1"
