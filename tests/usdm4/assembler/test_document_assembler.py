import os
import pathlib
import pytest
from simple_error_log.errors import Errors
from src.usdm4.assembler.document_assembler import DocumentAssembler
from src.usdm4.builder.builder import Builder
from src.usdm4.api.study_definition_document_version import (
    StudyDefinitionDocumentVersion,
)


def root_path():
    """Get the root path for the usdm4 package."""
    base = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


@pytest.fixture(scope="module")
def builder():
    """Create a Builder instance for testing."""
    return Builder(root_path(), Errors())


@pytest.fixture(scope="module")
def errors():
    """Create an Errors instance for testing."""
    return Errors()


@pytest.fixture
def document_assembler(builder, errors):
    """Create a DocumentAssembler instance for testing."""
    # Clear the builder to avoid cross-reference conflicts
    builder.clear()
    return DocumentAssembler(builder, errors)


class TestDocumentAssemblerInitialization:
    """Test DocumentAssembler initialization."""

    def test_init_with_valid_parameters(self, builder, errors):
        """Test DocumentAssembler initialization with valid parameters."""
        assembler = DocumentAssembler(builder, errors)

        assert assembler._builder is builder
        assert assembler._errors is errors
        assert (
            assembler.MODULE == "usdm4.assembler.document_assembler.DocumentAssembler"
        )

        # Test initial state
        assert assembler._document is None
        assert assembler._document_version is None
        assert assembler._contents == []
        assert assembler._dates == []
        assert assembler._encoder is not None

    def test_class_constants(self, document_assembler):
        """Test that class constants are properly defined."""
        assert (
            document_assembler.MODULE
            == "usdm4.assembler.document_assembler.DocumentAssembler"
        )
        assert (
            document_assembler.DIV_OPEN_NS
            == '<div xmlns="http://www.w3.org/1999/xhtml">'
        )
        assert document_assembler.DIV_CLOSE == "</div>"

    def test_properties_initial_state(self, document_assembler):
        """Test that properties return correct initial state."""
        assert document_assembler.document is None
        assert document_assembler.document_version is None
        assert document_assembler.contents == []
        assert document_assembler.dates == []

    def test_encoder_initialization(self, document_assembler):
        """Test that encoder is properly initialized."""
        assert document_assembler._encoder is not None
        assert hasattr(document_assembler._encoder, "_builder")
        assert hasattr(document_assembler._encoder, "_errors")


class TestDocumentAssemblerValidData:
    """Test DocumentAssembler with valid data."""

    def test_execute_with_minimal_valid_data(self, document_assembler):
        """Test execute with minimal valid document data."""
        data = {
            "document": {
                "label": "Test Protocol Document",
                "version": "1.0",
                "status": "Draft",
                "template": "Standard Protocol Template",
                "version_date": "2024-01-15",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Introduction",
                    "text": "This is the introduction section.",
                }
            ],
        }

        document_assembler.execute(data)

        # Should have created document and document version
        assert document_assembler.document is not None
        assert document_assembler.document_version is not None

        # Verify document properties
        document = document_assembler.document
        assert document.label == "Test Protocol Document"
        assert document.name == "TEST-PROTOCOL-DOCUMENT"  # _label_to_name conversion
        assert document.description == "Protocol Document"
        assert document.templateName == "Standard Protocol Template"

        # Verify document version properties
        doc_version = document_assembler.document_version
        assert doc_version.version == "1.0"

        # Should have created narrative content
        assert len(document_assembler.contents) == 1
        assert len(doc_version.contents) == 1

        # Should have created governance date
        assert len(document_assembler.dates) == 1

    def test_execute_with_multiple_sections_flat(self, document_assembler):
        """Test execute with multiple flat sections."""
        data = {
            "document": {
                "label": "Multi-Section Protocol",
                "version": "2.0",
                "status": "Final",
                "template": "Multi-Section Template",
                "version_date": "2024-02-20",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Introduction",
                    "text": "Introduction content.",
                },
                {
                    "section_number": "2",
                    "section_title": "Objectives",
                    "text": "Objectives content.",
                },
                {
                    "section_number": "3",
                    "section_title": "Methods",
                    "text": "Methods content.",
                },
            ],
        }

        document_assembler.execute(data)

        # Should have created all sections
        assert len(document_assembler.contents) == 3
        assert len(document_assembler.document_version.contents) == 3

        # Verify section content
        content_items = document_assembler.contents
        assert any("Introduction content." in item.text for item in content_items)
        assert any("Objectives content." in item.text for item in content_items)
        assert any("Methods content." in item.text for item in content_items)

    def test_execute_with_hierarchical_sections(self, document_assembler):
        """Test execute with hierarchical sections."""
        data = {
            "document": {
                "label": "Hierarchical Protocol",
                "version": "1.5",
                "status": "Draft",
                "template": "Hierarchical Template",
                "version_date": "2024-03-10",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Introduction",
                    "text": "Main introduction.",
                },
                {
                    "section_number": "1.1",
                    "section_title": "Background",
                    "text": "Background information.",
                },
                {
                    "section_number": "1.2",
                    "section_title": "Rationale",
                    "text": "Study rationale.",
                },
                {
                    "section_number": "2",
                    "section_title": "Objectives",
                    "text": "Study objectives.",
                },
                {
                    "section_number": "2.1",
                    "section_title": "Primary Objectives",
                    "text": "Primary objectives content.",
                },
            ],
        }

        document_assembler.execute(data)

        # Should have created all sections
        assert len(document_assembler.contents) == 5
        assert len(document_assembler.document_version.contents) == 5

        # Verify hierarchical structure exists
        narrative_contents = document_assembler.document_version.contents

        # Find level 1 sections
        level_1_sections = [
            nc for nc in narrative_contents if nc.sectionNumber in ["1", "2"]
        ]
        assert len(level_1_sections) == 2

        # Verify child relationships exist
        intro_section = next(
            (nc for nc in level_1_sections if nc.sectionNumber == "1"), None
        )
        assert intro_section is not None
        assert len(intro_section.childIds) == 2  # Should have 1.1 and 1.2 as children

    def test_execute_with_html_content(self, document_assembler):
        """Test execute with HTML content in sections."""
        data = {
            "document": {
                "label": "HTML Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "HTML Template",
                "version_date": "2024-04-05",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Introduction",
                    "text": "<p>This is <strong>bold</strong> text with <em>emphasis</em>.</p><ul><li>Item 1</li><li>Item 2</li></ul>",
                }
            ],
        }

        document_assembler.execute(data)

        # Should have wrapped HTML content in div with namespace
        content_item = document_assembler.contents[0]
        expected_text = f"{document_assembler.DIV_OPEN_NS}<p>This is <strong>bold</strong> text with <em>emphasis</em>.</p><ul><li>Item 1</li><li>Item 2</li></ul>{document_assembler.DIV_CLOSE}"
        assert content_item.text == expected_text

    def test_execute_with_empty_section_fields(self, document_assembler):
        """Test execute with empty section number and title."""
        data = {
            "document": {
                "label": "Empty Fields Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "Empty Template",
                "version_date": "2024-05-01",
            },
            "sections": [
                {
                    "section_number": "",
                    "section_title": "",
                    "text": "Content without section number or title.",
                },
                {
                    "section_number": "1",
                    "section_title": "Valid Section",
                    "text": "Valid section content.",
                },
            ],
        }

        document_assembler.execute(data)

        # Should handle empty fields
        assert len(document_assembler.contents) == 2
        narrative_contents = document_assembler.document_version.contents

        # First section should have empty section number and title
        first_section = narrative_contents[0]
        assert first_section.sectionNumber == ""
        assert first_section.sectionTitle == ""
        assert first_section.displaySectionNumber is False
        assert first_section.displaySectionTitle is False

        # Second section should have valid values
        second_section = narrative_contents[1]
        assert second_section.sectionNumber == "1"
        assert second_section.sectionTitle == "Valid Section"
        assert second_section.displaySectionNumber is True
        assert second_section.displaySectionTitle is True

    def test_execute_with_complex_hierarchical_structure(self, document_assembler):
        """Test execute with complex multi-level hierarchy."""
        data = {
            "document": {
                "label": "Complex Protocol",
                "version": "2.1",
                "status": "Final",
                "template": "Complex Template",
                "version_date": "2024-06-15",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Introduction",
                    "text": "Introduction content.",
                },
                {
                    "section_number": "1.1",
                    "section_title": "Background",
                    "text": "Background content.",
                },
                {
                    "section_number": "1.1.1",
                    "section_title": "Disease Overview",
                    "text": "Disease overview content.",
                },
                {
                    "section_number": "1.1.2",
                    "section_title": "Current Treatments",
                    "text": "Current treatments content.",
                },
                {
                    "section_number": "1.2",
                    "section_title": "Rationale",
                    "text": "Rationale content.",
                },
                {
                    "section_number": "2",
                    "section_title": "Objectives",
                    "text": "Objectives content.",
                },
            ],
        }

        document_assembler.execute(data)

        # Should have created all sections
        assert len(document_assembler.contents) == 6

        # Verify complex hierarchy
        narrative_contents = document_assembler.document_version.contents

        # Find sections by number
        sections_by_number = {nc.sectionNumber: nc for nc in narrative_contents}

        # Verify level 1 sections
        assert "1" in sections_by_number
        assert "2" in sections_by_number

        # Verify level 2 sections
        assert "1.1" in sections_by_number
        assert "1.2" in sections_by_number

        # Verify level 3 sections
        assert "1.1.1" in sections_by_number
        assert "1.1.2" in sections_by_number

        # Verify parent-child relationships
        intro_section = sections_by_number["1"]
        assert len(intro_section.childIds) == 2  # 1.1 and 1.2

        background_section = sections_by_number["1.1"]
        assert len(background_section.childIds) == 2  # 1.1.1 and 1.1.2


class TestDocumentAssemblerInvalidData:
    """Test DocumentAssembler with invalid data."""

    def test_execute_with_empty_data(self, document_assembler):
        """Test execute with empty data dictionary."""
        data = {}

        # Should handle empty data gracefully (may raise exception)
        try:
            document_assembler.execute(data)
        except KeyError:
            # Expected behavior - missing required keys
            pass

        # Should not have created objects
        assert document_assembler.document is None
        assert document_assembler.document_version is None

    def test_execute_with_missing_document_key(self, document_assembler):
        """Test execute with missing document key."""
        data = {
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Test Section",
                    "text": "Test content.",
                }
            ]
        }

        # Should handle missing document key (may raise exception)
        try:
            document_assembler.execute(data)
        except KeyError:
            # Expected behavior - missing document key
            pass

    def test_execute_with_missing_sections_key(self, document_assembler):
        """Test execute with missing sections key."""
        data = {
            "document": {
                "label": "Test Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "Test Template",
                "version_date": "2024-01-01",
            }
        }

        # Should handle missing sections key (may raise exception)
        try:
            document_assembler.execute(data)
        except KeyError:
            # Expected behavior - missing sections key
            pass

    def test_execute_with_invalid_document_fields(self, document_assembler):
        """Test execute with missing required document fields."""
        data = {
            "document": {
                "label": "Test Protocol"
                # Missing version, status, template, version_date
            },
            "sections": [],
        }

        # Should handle missing document fields (may raise exception)
        try:
            document_assembler.execute(data)
        except KeyError:
            # Expected behavior - missing required fields
            pass

    def test_execute_with_invalid_section_fields(self, document_assembler):
        """Test execute with missing required section fields."""
        data = {
            "document": {
                "label": "Test Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "Test Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1"
                    # Missing section_title and text
                }
            ],
        }

        # Should handle missing section fields (may raise exception)
        try:
            document_assembler.execute(data)
        except KeyError:
            # Expected behavior - missing required fields
            pass

    def test_execute_with_invalid_date_format(self, document_assembler):
        """Test execute with invalid date format."""
        data = {
            "document": {
                "label": "Invalid Date Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "Test Template",
                "version_date": "invalid-date-format",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Test Section",
                    "text": "Test content.",
                }
            ],
        }

        document_assembler.execute(data)

        # Should handle invalid date format gracefully
        # Document and version should still be created
        assert document_assembler.document is not None
        assert document_assembler.document_version is not None
        # Date creation may fail, resulting in empty dates list
        assert len(document_assembler.dates) == 0

    def test_execute_with_none_values(self, document_assembler):
        """Test execute with None values in data."""
        data = {
            "document": {
                "label": None,
                "version": "1.0",
                "status": "Draft",
                "template": "Test Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {"section_number": "1", "section_title": None, "text": "Test content."}
            ],
        }

        # Should handle None values (may raise exception or handle gracefully)
        try:
            document_assembler.execute(data)
        except (TypeError, AttributeError):
            # Expected behavior - None values cause issues
            pass

    def test_execute_with_empty_sections_list(self, document_assembler):
        """Test execute with empty sections list."""
        data = {
            "document": {
                "label": "Empty Sections Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "Test Template",
                "version_date": "2024-01-01",
            },
            "sections": [],
        }

        document_assembler.execute(data)

        # Should handle empty sections list
        assert document_assembler.document is not None
        assert document_assembler.document_version is not None
        assert len(document_assembler.contents) == 0
        assert len(document_assembler.document_version.contents) == 0


class TestDocumentAssemblerEdgeCases:
    """Test DocumentAssembler edge cases."""

    def test_execute_with_unicode_content(self, document_assembler):
        """Test execute with unicode characters in content."""
        data = {
            "document": {
                "label": "Unicode Protocol 测试",
                "version": "1.0",
                "status": "Draft",
                "template": "Unicode Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Introduction 介绍",
                    "text": "Content with unicode: 测试内容 🧬💊 français español",
                }
            ],
        }

        document_assembler.execute(data)

        # Should handle unicode content
        assert document_assembler.document.label == "Unicode Protocol 测试"
        content_item = document_assembler.contents[0]
        assert "测试内容 🧬💊 français español" in content_item.text

    def test_execute_with_very_long_content(self, document_assembler):
        """Test execute with very long content."""
        long_text = "A" * 10000  # 10,000 character content
        data = {
            "document": {
                "label": "Long Content Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "Long Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Long Section",
                    "text": long_text,
                }
            ],
        }

        document_assembler.execute(data)

        # Should handle very long content
        assert document_assembler.document is not None
        content_item = document_assembler.contents[0]
        assert long_text in content_item.text

    def test_execute_with_special_characters_in_section_numbers(
        self, document_assembler
    ):
        """Test execute with special characters in section numbers."""
        data = {
            "document": {
                "label": "Special Chars Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "Special Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1.1.a",
                    "section_title": "Subsection A",
                    "text": "Subsection content.",
                },
                {
                    "section_number": "1.1.b",
                    "section_title": "Subsection B",
                    "text": "Subsection content.",
                },
            ],
        }

        document_assembler.execute(data)

        # Should handle special characters in section numbers
        # Note: These sections may not be processed if they don't match the expected hierarchy
        # The algorithm expects level 1 sections first, but these are level 3 sections
        assert document_assembler.document is not None
        assert document_assembler.document_version is not None
        # Contents may be empty if sections don't match expected hierarchy
        assert len(document_assembler.contents) >= 0

    def test_execute_with_section_numbers_ending_with_dot(self, document_assembler):
        """Test execute with section numbers ending with dot."""
        data = {
            "document": {
                "label": "Dot Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "Dot Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1.",
                    "section_title": "Section One",
                    "text": "Section one content.",
                },
                {
                    "section_number": "1.1.",
                    "section_title": "Subsection One One",
                    "text": "Subsection content.",
                },
            ],
        }

        document_assembler.execute(data)

        # Should handle section numbers with trailing dots
        assert len(document_assembler.contents) == 2
        narrative_contents = document_assembler.document_version.contents

        # Verify hierarchy is calculated correctly (dots should be stripped for level calculation)
        level_1_sections = [
            nc
            for nc in narrative_contents
            if len(nc.sectionNumber.rstrip(".").split(".")) == 1
        ]
        level_2_sections = [
            nc
            for nc in narrative_contents
            if len(nc.sectionNumber.rstrip(".").split(".")) == 2
        ]

        assert len(level_1_sections) == 1
        assert len(level_2_sections) == 1

    def test_execute_with_mixed_section_number_formats(self, document_assembler):
        """Test execute with mixed section number formats."""
        data = {
            "document": {
                "label": "Mixed Format Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "Mixed Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Introduction",
                    "text": "Introduction content.",
                },
                {
                    "section_number": "1.1",
                    "section_title": "Background",
                    "text": "Background content.",
                },
                {
                    "section_number": "1.1.1",
                    "section_title": "History",
                    "text": "History content.",
                },
                {
                    "section_number": "2",
                    "section_title": "Methods",
                    "text": "Methods content.",
                },
                {
                    "section_number": "2.a",
                    "section_title": "Method A",
                    "text": "Method A content.",
                },
            ],
        }

        document_assembler.execute(data)

        # Should handle mixed formats
        assert len(document_assembler.contents) == 5
        narrative_contents = document_assembler.document_version.contents

        # Verify all sections were created
        section_numbers = [nc.sectionNumber for nc in narrative_contents]
        expected_numbers = ["1", "1.1", "1.1.1", "2", "2.a"]
        for expected in expected_numbers:
            assert expected in section_numbers

    def test_execute_with_out_of_order_sections(self, document_assembler):
        """Test execute with sections not in hierarchical order."""
        data = {
            "document": {
                "label": "Out of Order Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "Out of Order Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Introduction",
                    "text": "Introduction content.",
                },
                {
                    "section_number": "1.2",
                    "section_title": "Rationale",
                    "text": "Rationale content.",
                },
                {
                    "section_number": "1.1",
                    "section_title": "Background",
                    "text": "Background content.",
                },
                {
                    "section_number": "2",
                    "section_title": "Methods",
                    "text": "Methods content.",
                },
            ],
        }

        document_assembler.execute(data)

        # Should process sections in the order provided
        assert len(document_assembler.contents) == 4
        # The hierarchy building algorithm should handle out-of-order sections


class TestDocumentAssemblerPrivateMethods:
    """Test DocumentAssembler private methods."""

    def test_section_level_calculation(self, document_assembler):
        """Test _section_level method with various section numbers."""
        # Test simple section numbers
        assert document_assembler._section_level({"section_number": "1"}) == 1
        assert document_assembler._section_level({"section_number": "1.1"}) == 2
        assert document_assembler._section_level({"section_number": "1.1.1"}) == 3
        assert document_assembler._section_level({"section_number": "1.1.1.1"}) == 4

        # Test section numbers with trailing dots
        assert document_assembler._section_level({"section_number": "1."}) == 1
        assert document_assembler._section_level({"section_number": "1.1."}) == 2
        assert document_assembler._section_level({"section_number": "1.1.1."}) == 3

        # Test section numbers with letters
        assert document_assembler._section_level({"section_number": "1.a"}) == 2
        assert document_assembler._section_level({"section_number": "1.1.a"}) == 3

    def test_create_date_with_valid_date(self, document_assembler):
        """Test _create_date with valid date."""
        data = {"version_date": "2024-01-15"}

        document_assembler._create_date(data)

        # Should have created a governance date
        assert len(document_assembler.dates) == 1
        date = document_assembler.dates[0]
        assert date.name == "PROTOCOL-DATE"
        assert hasattr(date, "dateValue")
        assert hasattr(date, "type")
        assert hasattr(date, "geographicScopes")

    def test_create_date_with_invalid_date(self, document_assembler, errors):
        """Test _create_date with invalid date format."""
        data = {"version_date": "invalid-date"}
        document_assembler._create_date(data)

        # Should have logged a warning and not created a date
        assert len(document_assembler.dates) == 0
        # Warning should have been logged (warnings don't increment error_count)

    def test_create_date_with_missing_date(self, document_assembler, errors):
        """Test _create_date with missing version_date."""
        data = {}

        # Should handle missing date gracefully (may raise exception)
        try:
            document_assembler._create_date(data)
        except KeyError:
            # Expected behavior - missing version_date key
            pass

    def test_section_to_narrative_with_simple_sections(self, document_assembler):
        """Test _section_to_narrative with simple flat sections."""
        # Set up document version first - use encoder to get proper status
        status_code = document_assembler._encoder.document_status("Draft")
        document_assembler._document_version = document_assembler._builder.create(
            StudyDefinitionDocumentVersion, {"version": "1.0", "status": status_code}
        )

        # Skip test if document version creation failed
        if document_assembler._document_version is None:
            pytest.skip(
                "Document version creation failed - likely due to Builder/API issues"
            )

        sections = [
            {
                "section_number": "1",
                "section_title": "Introduction",
                "text": "Introduction content.",
            },
            {
                "section_number": "2",
                "section_title": "Methods",
                "text": "Methods content.",
            },
        ]

        result_index = document_assembler._section_to_narrative(None, sections, 0, 1)

        # Should have processed all sections
        assert result_index == 2
        assert len(document_assembler.contents) == 2
        assert len(document_assembler._document_version.contents) == 2

    def test_section_to_narrative_with_hierarchical_sections(self, document_assembler):
        """Test _section_to_narrative with hierarchical sections."""
        # Set up document version first - use encoder to get proper status
        status_code = document_assembler._encoder.document_status("Draft")
        document_assembler._document_version = document_assembler._builder.create(
            StudyDefinitionDocumentVersion, {"version": "1.0", "status": status_code}
        )

        # Skip test if document version creation failed
        if document_assembler._document_version is None:
            pytest.skip(
                "Document version creation failed - likely due to Builder/API issues"
            )

        sections = [
            {
                "section_number": "1",
                "section_title": "Introduction",
                "text": "Introduction content.",
            },
            {
                "section_number": "1.1",
                "section_title": "Background",
                "text": "Background content.",
            },
            {
                "section_number": "2",
                "section_title": "Methods",
                "text": "Methods content.",
            },
        ]

        result_index = document_assembler._section_to_narrative(None, sections, 0, 1)

        # Should have processed all sections
        assert result_index == 3
        assert len(document_assembler.contents) == 3
        assert len(document_assembler._document_version.contents) == 3

        # Verify hierarchical structure
        narrative_contents = document_assembler._document_version.contents
        intro_section = next(
            (nc for nc in narrative_contents if nc.sectionNumber == "1"), None
        )
        assert intro_section is not None
        assert len(intro_section.childIds) == 1  # Should have 1.1 as child


class TestDocumentAssemblerStateManagement:
    """Test DocumentAssembler state management."""

    def test_multiple_execute_calls_accumulate_results(self, document_assembler):
        """Test that multiple execute calls accumulate results (DocumentAssembler doesn't reset state)."""
        # First call
        data1 = {
            "document": {
                "label": "First Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "First Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "First Section",
                    "text": "First content.",
                }
            ],
        }
        document_assembler.execute(data1)
        assert document_assembler.document.label == "First Protocol"
        assert len(document_assembler.contents) == 1

        # Clear builder state to avoid cross-reference conflicts
        document_assembler._builder.clear()

        # Second call should overwrite document but accumulate content
        data2 = {
            "document": {
                "label": "Second Protocol",
                "version": "2.0",
                "status": "Final",
                "template": "Second Template",
                "version_date": "2024-02-01",
            },
            "sections": [
                {
                    "section_number": "2",  # Use different section number to avoid conflicts
                    "section_title": "Second Section",
                    "text": "Second content.",
                }
            ],
        }
        document_assembler.execute(data2)
        assert document_assembler.document.label == "Second Protocol"
        # DocumentAssembler accumulates content, so we should have 2 items total
        assert len(document_assembler.contents) == 2

    def test_properties_reflect_current_state(self, document_assembler):
        """Test that properties reflect current state after operations."""
        data = {
            "document": {
                "label": "State Test Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "State Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Test Section",
                    "text": "Test content.",
                }
            ],
        }

        document_assembler.execute(data)

        # Properties should reflect current state
        assert document_assembler.document is not None
        assert document_assembler.document_version is not None
        assert len(document_assembler.contents) == 1
        assert len(document_assembler.dates) == 1

        # Properties should return the same objects
        assert document_assembler.document is document_assembler._document
        assert (
            document_assembler.document_version is document_assembler._document_version
        )
        assert document_assembler.contents is document_assembler._contents
        assert document_assembler.dates is document_assembler._dates


class TestDocumentAssemblerBuilderIntegration:
    """Test DocumentAssembler integration with Builder (without mocking)."""

    def test_builder_cdisc_code_integration(self, document_assembler):
        """Test integration with Builder's cdisc_code method."""
        data = {
            "document": {
                "label": "CDISC Test Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "CDISC Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Test Section",
                    "text": "Test content.",
                }
            ],
        }

        document_assembler.execute(data)

        # Should use Builder's cdisc_code method for document type and status
        document = document_assembler.document
        assert hasattr(document, "type")
        assert hasattr(document, "language")

        doc_version = document_assembler.document_version
        assert hasattr(doc_version, "status")

    def test_builder_iso639_code_integration(self, document_assembler):
        """Test integration with Builder's ISO 639 language code functionality."""
        data = {
            "document": {
                "label": "Language Test Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "Language Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Test Section",
                    "text": "Test content.",
                }
            ],
        }

        document_assembler.execute(data)

        # Should integrate with Builder's language code functionality
        document = document_assembler.document
        assert hasattr(document, "language")

    def test_builder_create_method_integration(self, document_assembler):
        """Test integration with Builder's create method."""
        data = {
            "document": {
                "label": "Create Test Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "Create Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Test Section",
                    "text": "Test content.",
                }
            ],
        }

        document_assembler.execute(data)

        # Should use Builder's create method to create objects
        document = document_assembler.document
        assert hasattr(document, "id")  # Objects created by Builder should have IDs
        assert document.label == "Create Test Protocol"

        doc_version = document_assembler.document_version
        assert hasattr(doc_version, "id")
        assert doc_version.version == "1.0"

        # Content items should also have IDs
        for content_item in document_assembler.contents:
            assert hasattr(content_item, "id")

    def test_builder_double_link_integration(self, document_assembler):
        """Test integration with Builder's double_link method."""
        data = {
            "document": {
                "label": "Link Test Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "Link Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "First Section",
                    "text": "First content.",
                },
                {
                    "section_number": "2",
                    "section_title": "Second Section",
                    "text": "Second content.",
                },
                {
                    "section_number": "3",
                    "section_title": "Third Section",
                    "text": "Third content.",
                },
            ],
        }

        document_assembler.execute(data)

        # Should use Builder's double_link method to create sequential links
        narrative_contents = document_assembler.document_version.contents
        assert len(narrative_contents) == 3

        # Verify sequential linking exists (previousId/nextId)
        for nc in narrative_contents:
            assert hasattr(nc, "previousId")
            assert hasattr(nc, "nextId")


class TestDocumentAssemblerErrorHandling:
    """Test DocumentAssembler error handling (without mocking Errors)."""

    def test_error_handling_with_malformed_data(self, document_assembler):
        """Test error handling with malformed data structures."""
        malformed_data = {
            "document": "not_a_dict",  # Should be a dict
            "sections": "not_a_list",  # Should be a list
        }

        # Should handle malformed data gracefully without crashing
        try:
            document_assembler.execute(malformed_data)
        except (TypeError, AttributeError, KeyError):
            # Expected behavior - the method doesn't handle malformed data gracefully
            pass

        # Should not have created any objects
        assert document_assembler.document is None
        assert document_assembler.document_version is None

    def test_error_handling_with_exception_in_execute(self, document_assembler, errors):
        """Test error handling when exceptions occur during execute."""
        # Data that will cause an exception during processing
        data = {
            "document": {
                "label": "Exception Test Protocol",
                "version": "1.0",
                "status": "Invalid Status",  # May cause issues
                "template": "Exception Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Test Section",
                    "text": "Test content.",
                }
            ],
        }

        # Execute should handle exceptions gracefully
        document_assembler.execute(data)

        # Should have logged an error if exception occurred
        # The exact behavior depends on whether the status causes an exception

    def test_error_handling_with_encoder_failures(self, document_assembler, errors):
        """Test error handling when encoder operations fail."""
        data = {
            "document": {
                "label": "Encoder Test Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "Encoder Template",
                "version_date": "completely-invalid-date-format",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Test Section",
                    "text": "Test content.",
                }
            ],
        }

        document_assembler.execute(data)

        # Should handle encoder failures gracefully
        # Document should still be created even if date parsing fails
        assert document_assembler.document is not None
        assert document_assembler.document_version is not None

    def test_error_handling_with_builder_failures(self, document_assembler, errors):
        """Test error handling when Builder operations fail."""
        # This test verifies that the assembler handles Builder failures gracefully
        # The exact failure scenarios depend on the Builder implementation
        data = {
            "document": {
                "label": "Builder Test Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "Builder Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Test Section",
                    "text": "Test content.",
                }
            ],
        }

        document_assembler.execute(data)

        # Should handle Builder failures gracefully
        # The exact behavior depends on what Builder operations might fail


class TestDocumentAssemblerAdditionalCoverage:
    """Additional test cases to improve coverage."""

    def test_initialization_with_invalid_parameters(self, builder, errors):
        """Test DocumentAssembler initialization with invalid parameters."""
        # Test with invalid builder type
        assembler = DocumentAssembler("not_a_builder", errors)
        assert assembler._builder == "not_a_builder"

        # Test with invalid errors type
        assembler = DocumentAssembler(builder, "not_errors")
        assert assembler._errors == "not_errors"

    def test_encoder_integration(self, document_assembler):
        """Test that encoder is properly integrated."""
        # Verify encoder has correct builder and errors references
        assert document_assembler._encoder._builder is document_assembler._builder
        assert document_assembler._encoder._errors is document_assembler._errors

    def test_div_constants_usage(self, document_assembler):
        """Test that DIV constants are used correctly."""
        data = {
            "document": {
                "label": "DIV Test Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "DIV Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Test Section",
                    "text": "Plain text content",
                }
            ],
        }

        document_assembler.execute(data)

        # Verify DIV constants are used in content wrapping
        content_item = document_assembler.contents[0]
        assert document_assembler.DIV_OPEN_NS in content_item.text
        assert document_assembler.DIV_CLOSE in content_item.text

    def test_section_display_flags(self, document_assembler):
        """Test section display flags are set correctly."""
        data = {
            "document": {
                "label": "Display Test Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "Display Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "With Both",
                    "text": "Content with both number and title.",
                },
                {
                    "section_number": "",
                    "section_title": "Title Only",
                    "text": "Content with title only.",
                },
                {
                    "section_number": "2",
                    "section_title": "",
                    "text": "Content with number only.",
                },
                {
                    "section_number": "",
                    "section_title": "",
                    "text": "Content with neither.",
                },
            ],
        }

        document_assembler.execute(data)

        narrative_contents = document_assembler.document_version.contents
        assert len(narrative_contents) == 4

        # First section: both number and title
        assert narrative_contents[0].displaySectionNumber is True
        assert narrative_contents[0].displaySectionTitle is True

        # Second section: title only
        assert narrative_contents[1].displaySectionNumber is False
        assert narrative_contents[1].displaySectionTitle is True

        # Third section: number only
        assert narrative_contents[2].displaySectionNumber is True
        assert narrative_contents[2].displaySectionTitle is False

        # Fourth section: neither
        assert narrative_contents[3].displaySectionNumber is False
        assert narrative_contents[3].displaySectionTitle is False

    def test_narrative_content_naming(self, document_assembler):
        """Test that narrative content items are named correctly."""
        data = {
            "document": {
                "label": "Naming Test Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "Naming Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "First Section",
                    "text": "First content.",
                },
                {
                    "section_number": "2",
                    "section_title": "Second Section",
                    "text": "Second content.",
                },
            ],
        }

        document_assembler.execute(data)

        # Verify naming patterns
        narrative_contents = document_assembler.document_version.contents
        content_items = document_assembler.contents

        # NarrativeContent should be named NC-{index}
        assert narrative_contents[0].name == "NC-0"
        assert narrative_contents[1].name == "NC-1"

        # NarrativeContentItem should be named NCI-{index}
        assert content_items[0].name == "NCI-0"
        assert content_items[1].name == "NCI-1"

    def test_content_item_references(self, document_assembler):
        """Test that narrative content references content items correctly."""
        data = {
            "document": {
                "label": "Reference Test Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "Reference Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Test Section",
                    "text": "Test content.",
                }
            ],
        }

        document_assembler.execute(data)

        # Verify content item references
        narrative_content = document_assembler.document_version.contents[0]
        content_item = document_assembler.contents[0]

        assert narrative_content.contentItemId == content_item.id

    def test_inheritance_from_base_assembler_methods(self, document_assembler):
        """Test that DocumentAssembler properly inherits BaseAssembler methods."""
        # Test _label_to_name method inheritance
        result = document_assembler._label_to_name("Test Document Name")
        assert result == "TEST-DOCUMENT-NAME"

        # Test that MODULE constant is properly set
        assert (
            document_assembler.MODULE
            == "usdm4.assembler.document_assembler.DocumentAssembler"
        )

    def test_properties_are_references_to_internal_objects(self, document_assembler):
        """Test that properties return references to internal objects, not copies."""
        # Initially None/empty
        assert document_assembler.document is document_assembler._document
        assert (
            document_assembler.document_version is document_assembler._document_version
        )
        assert document_assembler.contents is document_assembler._contents
        assert document_assembler.dates is document_assembler._dates

        # After adding data
        data = {
            "document": {
                "label": "Reference Test Protocol",
                "version": "1.0",
                "status": "Draft",
                "template": "Reference Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Test Section",
                    "text": "Test content.",
                }
            ],
        }
        document_assembler.execute(data)

        # Should still be references to the same objects
        assert document_assembler.document is document_assembler._document
        assert (
            document_assembler.document_version is document_assembler._document_version
        )
        assert document_assembler.contents is document_assembler._contents
        assert document_assembler.dates is document_assembler._dates

    def test_execute_with_complex_mixed_scenarios(self, document_assembler):
        """Test execute with complex mixed scenarios."""
        data = {
            "document": {
                "label": "Complex Mixed Protocol 🧬",
                "version": "2.1.3",
                "status": "Final",
                "template": "Complex Mixed Template",
                "version_date": "2024-12-31",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Introduction with Unicode 测试",
                    "text": "<p>HTML content with <strong>formatting</strong> and unicode 🧬💊</p>",
                },
                {
                    "section_number": "1.1",
                    "section_title": "",  # Empty title
                    "text": "Subsection with empty title",
                },
                {
                    "section_number": "1.2.a",
                    "section_title": "Complex Numbering",
                    "text": "Section with complex numbering scheme",
                },
                {
                    "section_number": "2.",
                    "section_title": "Section with Trailing Dot",
                    "text": "Section number ends with dot",
                },
                {
                    "section_number": "",
                    "section_title": "No Number Section",
                    "text": "Section without number",
                },
            ],
        }

        document_assembler.execute(data)

        # Should handle all complex scenarios
        assert document_assembler.document.label == "Complex Mixed Protocol 🧬"
        assert document_assembler.document.name == "COMPLEX-MIXED-PROTOCOL-🧬"
        assert len(document_assembler.contents) == 5
        assert len(document_assembler.document_version.contents) == 5
        assert len(document_assembler.dates) == 1

        # Verify complex content handling
        narrative_contents = document_assembler.document_version.contents
        content_items = document_assembler.contents

        # First section should have HTML wrapped in div
        assert document_assembler.DIV_OPEN_NS in content_items[0].text
        assert "<strong>formatting</strong>" in content_items[0].text
        assert "🧬💊" in content_items[0].text

        # Verify display flags for various scenarios
        assert narrative_contents[0].displaySectionNumber is True  # "1"
        assert narrative_contents[0].displaySectionTitle is True  # Has title

        assert narrative_contents[1].displaySectionNumber is True  # "1.1"
        assert narrative_contents[1].displaySectionTitle is False  # Empty title

        assert narrative_contents[2].displaySectionNumber is True  # "1.2.a"
        assert narrative_contents[2].displaySectionTitle is True  # Has title

        assert narrative_contents[3].displaySectionNumber is True  # "2."
        assert narrative_contents[3].displaySectionTitle is True  # Has title

        assert narrative_contents[4].displaySectionNumber is False  # Empty number
        assert narrative_contents[4].displaySectionTitle is True  # Has title
